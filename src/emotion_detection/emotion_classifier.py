# src/emotion_detection/emotion_classifier.py
from deepface import DeepFace
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class EmotionClassifier:
    def __init__(self):
        self.emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        self.emotion_translation = {
            'angry': 'Enojo',
            'disgust': 'Disgusto',
            'fear': 'Miedo',
            'happy': 'Felicidad',
            'sad': 'Tristeza',
            'surprise': 'Sorpresa',
            'neutral': 'Neutral'
        }
    
    def analyze_emotion(self, face_image):
        """
        Analiza la emoción en un rostro
        Retorna: (emoción principal, confianza, todas las emociones)
        """
        try:
            # Preprocesar imagen
            if face_image is None or face_image.size == 0:
                return None, 0, {}
            
            # Convertir a RGB si es necesario
            if len(face_image.shape) == 3 and face_image.shape[2] == 3:
                rgb_face = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            else:
                rgb_face = face_image
            
            # Analizar con DeepFace
            result = DeepFace.analyze(
                img_path=rgb_face,
                actions=['emotion'],
                enforce_detection=False,
                silent=True
            )
            
            if isinstance(result, list):
                result = result[0]
            
            # Obtener emociones y confianza
            emotions_dict = result['emotion']
            
            # Encontrar la emoción dominante
            dominant_emotion = result['dominant_emotion']
            confidence = emotions_dict[dominant_emotion] / 100.0
            
            # Traducir emoción
            translated_emotion = self.emotion_translation.get(dominant_emotion, dominant_emotion)
            
            # Crear diccionario con todas las emociones traducidas
            all_emotions = {}
            for eng_emo, value in emotions_dict.items():
                esp_emo = self.emotion_translation.get(eng_emo, eng_emo)
                all_emotions[esp_emo] = value / 100.0
            
            return translated_emotion, confidence, all_emotions
            
        except Exception as e:
            logger.error(f"Error al analizar emoción: {e}")
            return None, 0, {}
    
    def get_emotion_color(self, emotion):
        """Retorna un color para cada emoción (para visualización)"""
        colors = {
            'Felicidad': (0, 255, 0),    # Verde
            'Tristeza': (255, 0, 0),     # Azul
            'Enojo': (0, 0, 255),        # Rojo
            'Sorpresa': (255, 255, 0),   # Cyan
            'Miedo': (255, 0, 255),      # Magenta
            'Disgusto': (0, 255, 255),   # Amarillo
            'Neutral': (128, 128, 128)   # Gris
        }
        return colors.get(emotion, (255, 255, 255))
    
    def analyze_multiple_faces(self, faces_images):
        """
        Analiza emociones para múltiples rostros
        Retorna: Lista de resultados por rostro
        """
        results = []
        for face_img in faces_images:
            emotion, conf, all_emotions = self.analyze_emotion(face_img)
            results.append({
                'emotion': emotion,
                'confidence': conf,
                'all_emotions': all_emotions
            })
        return results
    