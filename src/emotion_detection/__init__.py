# src/emotion_detection/__init__.py
"""
Módulo de detección de emociones
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.emotion_detection.emotion_classifier import EmotionClassifier

__all__ = ['EmotionClassifier']