# src/face_recognition/__init__.py
"""
Módulo de reconocimiento facial
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.face_recognition.face_encoder import FaceEncoder
from src.face_recognition.face_recognizer import FaceRecognizer

__all__ = ['FaceEncoder', 'FaceRecognizer']