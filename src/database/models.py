# src/database/models.py
"""
Modelos de base de datos para el sistema de reconocimiento facial
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import numpy as np

# Crear la base declarativa
Base = declarative_base()

class Persona(Base):
    """Modelo para personas registradas"""
    __tablename__ = 'personas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    fecha_registro = Column(DateTime, default=datetime.now)
    embedding_rostro = Column(LargeBinary, nullable=True)
    
    # Relación con detecciones
    detecciones = relationship("Deteccion", back_populates="persona", cascade="all, delete-orphan")
    
    def set_embedding(self, embedding):
        """Convierte numpy array a bytes para guardar en BD"""
        if embedding is not None:
            self.embedding_rostro = embedding.tobytes()
            return True
        return False
    
    def get_embedding(self):
        """Recupera el embedding de bytes a numpy array"""
        if self.embedding_rostro:
            return np.frombuffer(self.embedding_rostro, dtype=np.float32)
        return None
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    def __repr__(self):
        return f"<Persona {self.nombre_completo}>"

class Deteccion(Base):
    """Modelo para detecciones emocionales"""
    __tablename__ = 'detecciones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    persona_id = Column(Integer, ForeignKey('personas.id', ondelete='CASCADE'), nullable=False)
    emocion_detectada = Column(String(50), nullable=False)
    nivel_confianza = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    imagen_path = Column(String(255), nullable=True)
    
    # Relación con persona
    persona = relationship("Persona", back_populates="detecciones")
    
    @property
    def confianza_porcentaje(self):
        return f"{self.nivel_confianza * 100:.1f}%"
    
    def __repr__(self):
        return f"<Deteccion {self.emocion_detectada} ({self.confianza_porcentaje})>"

# Exportar explícitamente las clases
__all__ = ['Base', 'Persona', 'Deteccion']