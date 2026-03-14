# src/database/database_manager.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definir Base aquí mismo para evitar problemas de importación
Base = declarative_base()

# Definir modelos aquí mismo
class Persona(Base):
    __tablename__ = 'personas'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    fecha_registro = Column(DateTime, default=datetime.now)
    embedding_rostro = Column(LargeBinary, nullable=False)
    
    detecciones = relationship("Deteccion", back_populates="persona", cascade="all, delete-orphan")
    
    def set_embedding(self, embedding):
        self.embedding_rostro = embedding.tobytes()
    
    def get_embedding(self):
        return np.frombuffer(self.embedding_rostro, dtype=np.float32)

class Deteccion(Base):
    __tablename__ = 'detecciones'
    
    id = Column(Integer, primary_key=True)
    persona_id = Column(Integer, ForeignKey('personas.id'), nullable=False)
    emocion_detectada = Column(String(50), nullable=False)
    nivel_confianza = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    imagen_path = Column(String(255), nullable=True)
    
    persona = relationship("Persona", back_populates="detecciones")

# Clase DatabaseManager - ¡ASEGÚRATE QUE ESTÁ DEFINIDA!
class DatabaseManager:
    def __init__(self, db_path='sqlite:///facial_recognition.db'):
        logger.info(f"Inicializando DatabaseManager con: {db_path}")
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info("DatabaseManager inicializado correctamente")
    
    def add_persona(self, nombre, apellido, email, embedding):
        session = self.Session()
        try:
            existing = session.query(Persona).filter_by(email=email).first()
            if existing:
                logger.warning(f"Persona con email {email} ya existe")
                return None
            
            nueva_persona = Persona(
                nombre=nombre,
                apellido=apellido,
                email=email
            )
            nueva_persona.set_embedding(embedding)
            
            session.add(nueva_persona)
            session.commit()
            logger.info(f"Persona {nombre} {apellido} registrada exitosamente")
            return nueva_persona.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error al agregar persona: {e}")
            return None
        finally:
            session.close()
    
    def get_all_personas(self):
        session = self.Session()
        try:
            personas = session.query(Persona).all()
            return [{
                'id': p.id,
                'nombre': p.nombre,
                'apellido': p.apellido,
                'email': p.email,
                'fecha_registro': p.fecha_registro,
                'embedding': p.get_embedding()
            } for p in personas]
        except Exception as e:
            logger.error(f"Error al obtener personas: {e}")
            return []
        finally:
            session.close()
    
    def add_deteccion(self, persona_id, emocion, confianza, imagen_path=None):
        session = self.Session()
        try:
            deteccion = Deteccion(
                persona_id=persona_id,
                emocion_detectada=emocion,
                nivel_confianza=confianza,
                imagen_path=imagen_path
            )
            session.add(deteccion)
            session.commit()
            return deteccion.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error al registrar detección: {e}")
            return None
        finally:
            session.close()
    
    def get_detecciones_by_persona(self, persona_id, days=None):
        session = self.Session()
        try:
            query = session.query(Deteccion).filter_by(persona_id=persona_id)
            
            if days:
                from datetime import datetime, timedelta
                fecha_limite = datetime.now() - timedelta(days=days)
                query = query.filter(Deteccion.timestamp >= fecha_limite)
            
            detecciones = query.order_by(Deteccion.timestamp.desc()).all()
            return [{
                'id': d.id,
                'emocion': d.emocion_detectada,
                'confianza': d.nivel_confianza,
                'timestamp': d.timestamp,
                'persona_nombre': d.persona.nombre + ' ' + d.persona.apellido
            } for d in detecciones]
        except Exception as e:
            logger.error(f"Error al obtener detecciones: {e}")
            return []
        finally:
            session.close()
    
    def get_estadisticas_emociones(self, days=30):
        session = self.Session()
        try:
            from datetime import datetime, timedelta
            fecha_limite = datetime.now() - timedelta(days=days)
            detecciones = session.query(Deteccion).filter(
                Deteccion.timestamp >= fecha_limite
            ).all()
            
            stats = {}
            for d in detecciones:
                emocion = d.emocion_detectada
                if emocion not in stats:
                    stats[emocion] = {'count': 0, 'confianza_promedio': 0}
                stats[emocion]['count'] += 1
                stats[emocion]['confianza_promedio'] += d.nivel_confianza
            
            for emocion in stats:
                stats[emocion]['confianza_promedio'] /= stats[emocion]['count']
            
            return stats
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {}
        finally:
            session.close()