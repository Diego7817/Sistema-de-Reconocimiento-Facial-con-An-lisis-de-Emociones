# src/face_recognition/face_recognizer.py
import numpy as np
from .face_encoder import FaceEncoder
import logging

logger = logging.getLogger(__name__)

class FaceRecognizer:
    def __init__(self, database_manager):
        self.encoder = FaceEncoder()
        self.db_manager = database_manager
        self.known_faces = []
        self.known_names = []
        self.known_ids = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Carga todos los rostros conocidos desde la base de datos"""
        try:
            personas = self.db_manager.get_all_personas()
            self.known_faces = []
            self.known_names = []
            self.known_ids = []
            
            for p in personas:
                if p['embedding'] is not None:
                    self.known_faces.append(p['embedding'])
                    self.known_names.append(f"{p['nombre']} {p['apellido']}")
                    self.known_ids.append(p['id'])
            
            logger.info(f"Cargados {len(self.known_faces)} rostros conocidos")
            
        except Exception as e:
            logger.error(f"Error al cargar rostros conocidos: {e}")
    
    def recognize_face(self, face_encoding, tolerance=0.6):
        """
        Reconoce un rostro entre los conocidos usando DeepFace
        Retorna: (id, nombre, distancia) o (None, "Desconocido", None)
        """
        if not self.known_faces or face_encoding is None:
            return None, "Desconocido", None
        
        try:
            best_match = self.encoder.find_best_match(
                self.known_faces, 
                face_encoding, 
                tolerance
            )
            
            if best_match:
                idx, distance = best_match
                return (self.known_ids[idx], 
                       self.known_names[idx], 
                       distance)
            else:
                return None, "Desconocido", None
                
        except Exception as e:
            logger.error(f"Error en reconocimiento facial: {e}")
            return None, "Error", None
    
    def add_new_face(self, nombre, apellido, email, face_encoding):
        """Agrega un nuevo rostro al sistema"""
        try:
            # Verificar si ya existe (por similitud facial)
            if self.known_faces:
                best_match = self.encoder.find_best_match(
                    self.known_faces, 
                    face_encoding, 
                    tolerance=0.5  # Umbral más estricto para evitar duplicados
                )
                
                if best_match:
                    idx, distance = best_match
                    logger.warning(f"Rostro similar ya registrado como {self.known_names[idx]} (distancia: {distance:.3f})")
                    return False, f"Rostro similar ya registrado como {self.known_names[idx]}"
            
            # Guardar en base de datos
            persona_id = self.db_manager.add_persona(
                nombre, apellido, email, face_encoding
            )
            
            if persona_id:
                # Actualizar lista en memoria
                self.known_faces.append(face_encoding)
                self.known_names.append(f"{nombre} {apellido}")
                self.known_ids.append(persona_id)
                return True, "Registro exitoso"
            else:
                return False, "Error al guardar en base de datos"
                
        except Exception as e:
            logger.error(f"Error al agregar nuevo rostro: {e}")
            return False, f"Error: {str(e)}"