# src/face_recognition/face_encoder.py
import cv2
import numpy as np
from deepface import DeepFace
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

class FaceEncoder:
    def __init__(self):
        """Inicializa el codificador facial usando DeepFace"""
        self.backend = 'opencv'  # Backend para detección de rostros
        self.model_name = 'Facenet'  # Modelo para embeddings (512 dimensiones)
        self.detector_backend = 'opencv'  # Detector de rostros
        logger.info(f"FaceEncoder inicializado con modelo: {self.model_name}")
    
    def extract_face_encoding(self, image):
        """
        Extrae el embedding facial usando DeepFace
        
        Args:
            image: Imagen en formato BGR (OpenCV)
            
        Returns:
            numpy.ndarray: Embedding facial o None si no se detecta rostro
        """
        temp_path = None
        try:
            # Convertir BGR a RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Guardar imagen temporalmente
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                temp_path = f.name
                cv2.imwrite(temp_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
            
            # Obtener embedding con DeepFace
            embedding_result = DeepFace.represent(
                img_path=temp_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False  # No lanzar error si no detecta rostro
            )
            
            if embedding_result and len(embedding_result) > 0:
                # DeepFace devuelve una lista, tomamos el primer rostro
                embedding = np.array(embedding_result[0]['embedding'])
                logger.debug(f"Embedding extraído: {embedding.shape}")
                return embedding
            
            logger.warning("No se detectó ningún rostro en la imagen")
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo embedding: {e}")
            return None
        finally:
            # Limpiar archivo temporal
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    
    def compare_faces(self, known_encoding, test_encoding, tolerance=0.6):
        """
        Compara dos embeddings faciales
        
        Args:
            known_encoding: Embedding conocido
            test_encoding: Embedding a comparar
            tolerance: Umbral de similitud (menor = más estricto)
            
        Returns:
            tuple: (coincide, distancia)
        """
        try:
            if known_encoding is None or test_encoding is None:
                return False, float('inf')
            
            # Calcular distancia euclidiana
            distance = np.linalg.norm(known_encoding - test_encoding)
            
            # Normalizar la distancia (valores típicos de FaceNet: 0-2)
            normalized_distance = distance / len(known_encoding)
            
            return distance <= tolerance, distance
            
        except Exception as e:
            logger.error(f"Error comparando rostros: {e}")
            return False, float('inf')
    
    def find_best_match(self, known_encodings, test_encoding, tolerance=0.6):
        """
        Encuentra la mejor coincidencia entre múltiples embeddings conocidos
        
        Args:
            known_encodings: Lista de embeddings conocidos
            test_encoding: Embedding a comparar
            tolerance: Umbral de similitud
            
        Returns:
            tuple: (índice, distancia) de la mejor coincidencia o None
        """
        if not known_encodings or test_encoding is None:
            return None
        
        best_idx = None
        best_distance = float('inf')
        
        for i, enc in enumerate(known_encodings):
            if enc is not None:
                _, distance = self.compare_faces(enc, test_encoding)
                if distance < best_distance:
                    best_distance = distance
                    best_idx = i
        
        if best_idx is not None and best_distance <= tolerance:
            return best_idx, best_distance
        return None
    
    def validate_face_quality(self, image):
        """
        Valida la calidad de la imagen facial
        
        Args:
            image: Imagen en formato BGR
            
        Returns:
            dict: Métricas de calidad
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detectar rostro con Haar Cascade (más rápido)
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            # Calcular nitidez (varianza del Laplaciano)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calcular brillo promedio
            brightness = np.mean(gray)
            
            # Calcular contraste (desviación estándar)
            contrast = np.std(gray)
            
            quality = {
                'face_detected': len(faces) > 0,
                'num_faces': len(faces),
                'sharpness': laplacian_var,
                'brightness': brightness,
                'contrast': contrast,
                'is_good_quality': (
                    laplacian_var > 80 and  # Nitidez suficiente
                    40 < brightness < 220 and  # Brillo adecuado
                    contrast > 30 and  # Contraste suficiente
                    len(faces) == 1  # Exactamente un rostro
                )
            }
            
            return quality
            
        except Exception as e:
            logger.error(f"Error validando calidad: {e}")
            return {
                'face_detected': False,
                'num_faces': 0,
                'sharpness': 0,
                'brightness': 0,
                'contrast': 0,
                'is_good_quality': False
            }