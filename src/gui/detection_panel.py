# src/gui/detection_panel.py
import cv2
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QFrame)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont
from src.face_recognition.face_recognizer import FaceRecognizer
from src.emotion_detection.emotion_classifier import EmotionClassifier
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DetectionPanel(QWidget):
    detection_signal = pyqtSignal(dict)
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.face_recognizer = FaceRecognizer(db_manager)
        self.emotion_classifier = EmotionClassifier()
        self.camera = None
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_frame)
        self.detection_active = False
        self.current_detections = []
        self.init_ui()
        
    def init_ui(self):
        """Inicializa la interfaz del panel de detección"""
        layout = QHBoxLayout(self)
        
        # Panel izquierdo - Video
        video_panel = QWidget()
        video_layout = QVBoxLayout(video_panel)
        
        video_group = QGroupBox("Video en Tiempo Real")
        video_view_layout = QVBoxLayout()
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("border: 2px solid #34495e; border-radius: 5px; background-color: #000;")
        video_view_layout.addWidget(self.video_label)
        
        # Controles de video
        controls_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("Iniciar Detección")
        self.btn_start.clicked.connect(self.start_detection)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        
        self.btn_stop = QPushButton("Detener")
        self.btn_stop.clicked.connect(self.stop_detection)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        
        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_stop)
        controls_layout.addStretch()
        
        video_view_layout.addLayout(controls_layout)
        video_group.setLayout(video_view_layout)
        video_layout.addWidget(video_group)
        
        # Panel derecho - Información
        info_panel = QWidget()
        info_panel.setMaximumWidth(350)
        info_layout = QVBoxLayout(info_panel)
        
        # Info de persona detectada
        person_group = QGroupBox("Persona Detectada")
        person_layout = QVBoxLayout()
        
        self.lbl_person_name = QLabel("---")
        self.lbl_person_name.setFont(QFont("Arial", 18, QFont.Bold))
        self.lbl_person_name.setAlignment(Qt.AlignCenter)
        self.lbl_person_name.setStyleSheet("color: #2c3e50; padding: 15px;")
        
        self.lbl_person_email = QLabel("---")
        self.lbl_person_email.setAlignment(Qt.AlignCenter)
        self.lbl_person_email.setStyleSheet("color: #7f8c8d; padding: 5px;")
        
        person_layout.addWidget(self.lbl_person_name)
        person_layout.addWidget(self.lbl_person_email)
        person_group.setLayout(person_layout)
        info_layout.addWidget(person_group)
        
        # Info de emoción
        emotion_group = QGroupBox("Emoción Detectada")
        emotion_layout = QVBoxLayout()
        
        self.lbl_emotion = QLabel("---")
        self.lbl_emotion.setFont(QFont("Arial", 28, QFont.Bold))
        self.lbl_emotion.setAlignment(Qt.AlignCenter)
        
        self.lbl_confidence = QLabel("Confianza: ---")
        self.lbl_confidence.setAlignment(Qt.AlignCenter)
        self.lbl_confidence.setStyleSheet("font-size: 14px; color: #34495e;")
        
        # Barra de confianza visual
        self.confidence_frame = QFrame()
        self.confidence_frame.setFixedHeight(25)
        self.confidence_frame.setStyleSheet("background-color: #ecf0f1; border-radius: 5px; border: 1px solid #bdc3c7;")
        
        self.confidence_bar = QFrame(self.confidence_frame)
        self.confidence_bar.setFixedHeight(25)
        self.confidence_bar.setStyleSheet("background-color: #27ae60; border-radius: 5px;")
        self.confidence_bar.setFixedWidth(0)
        
        emotion_layout.addWidget(self.lbl_emotion)
        emotion_layout.addWidget(self.lbl_confidence)
        emotion_layout.addWidget(self.confidence_frame)
        emotion_group.setLayout(emotion_layout)
        info_layout.addWidget(emotion_group)
        
        # Info de tiempo
        time_group = QGroupBox("Información de Tiempo")
        time_layout = QVBoxLayout()
        
        self.lbl_detection_time = QLabel("Tiempo: ---")
        self.lbl_detection_time.setStyleSheet("font-size: 14px; color: #34495e;")
        
        time_layout.addWidget(self.lbl_detection_time)
        time_group.setLayout(time_layout)
        info_layout.addWidget(time_group)
        
        # Estadísticas rápidas
        stats_group = QGroupBox("Estadísticas de la Sesión")
        stats_layout = QVBoxLayout()
        
        self.lbl_total_detections = QLabel("Detecciones en sesión: 0")
        self.lbl_unique_persons = QLabel("Personas distintas: 0")
        
        stats_layout.addWidget(self.lbl_total_detections)
        stats_layout.addWidget(self.lbl_unique_persons)
        stats_group.setLayout(stats_layout)
        info_layout.addWidget(stats_group)
        
        info_layout.addStretch()
        
        # Agregar paneles al layout principal
        layout.addWidget(video_panel, 3)
        layout.addWidget(info_panel, 1)
        
        # Inicializar contadores
        self.session_detections = 0
        self.session_persons = set()
        
    def start_detection(self):
        """Inicia la detección"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                logger.error("No se pudo abrir la cámara")
                return
            
            self.camera_timer.start(30)  # 30 ms ≈ 33 fps
            self.detection_active = True
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            logger.info("Detección iniciada")
            
            # Reiniciar contadores de sesión
            self.session_detections = 0
            self.session_persons = set()
            self.update_stats()
            
        except Exception as e:
            logger.error(f"Error al iniciar detección: {e}")
    
    def stop_detection(self):
        """Detiene la detección - MÉTODO CORREGIDO"""
        if hasattr(self, 'camera_timer') and self.camera_timer.isActive():
            self.camera_timer.stop()
        
        if hasattr(self, 'camera') and self.camera is not None:
            self.camera.release()
            self.camera = None
        
        self.detection_active = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.video_label.clear()
        
        # Limpiar información
        self.clear_info()
        logger.info("Detección detenida")
    
    def update_frame(self):
        """Actualiza el frame y realiza detección"""
        if self.camera is None:
            return
        
        ret, frame = self.camera.read()
        if not ret:
            return
        
        # Procesar frame para detección
        processed_frame = self.process_frame(frame)
        
        # Mostrar frame
        self.display_frame(processed_frame)
    
    def process_frame(self, frame):
        """Procesa el frame para reconocimiento y emociones"""
        # Copiar frame para dibujar
        display_frame = frame.copy()
        
        # Detectar rostros
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
        
        self.current_detections = []
        
        for (x, y, w, h) in faces:
            # Extraer región del rostro
            face_roi = frame[y:y+h, x:x+w]
            
            # Redimensionar para mejor procesamiento
            if w > 100:
                face_roi = cv2.resize(face_roi, (160, 160))
            
            # Reconocimiento facial
            face_encoding = self.face_recognizer.encoder.extract_face_encoding(face_roi)
            
            person_id = None
            person_name = "Desconocido"
            distance = None
            
            if face_encoding is not None:
                person_id, person_name, distance = self.face_recognizer.recognize_face(face_encoding)
            
            # Análisis de emociones
            emotion, confidence, all_emotions = self.emotion_classifier.analyze_emotion(face_roi)
            
            # Guardar detección
            detection = {
                'person_id': person_id,
                'person_name': person_name,
                'distance': distance,
                'emotion': emotion,
                'confidence': confidence,
                'all_emotions': all_emotions,
                'bbox': (x, y, w, h)
            }
            self.current_detections.append(detection)
            
            # Actualizar estadísticas de sesión
            if person_name != "Desconocido" and person_name != "Error":
                self.session_detections += 1
                if person_id:
                    self.session_persons.add(person_id)
            
            # Registrar en base de datos si es persona conocida
            if person_id and emotion:
                try:
                    self.db_manager.add_deteccion(person_id, emotion, confidence)
                except Exception as e:
                    logger.error(f"Error guardando detección: {e}")
            
            # Dibujar en el frame
            self.draw_detection(display_frame, detection)
        
        # Actualizar información en GUI
        if self.current_detections:
            self.update_info(self.current_detections[0])  # Mostrar primera detección
        else:
            self.clear_info()
        
        # Actualizar estadísticas
        self.update_stats()
        
        # Actualizar tiempo
        current_time = datetime.now().strftime("%H:%M:%S")
        self.lbl_detection_time.setText(f"Tiempo: {current_time}")
        
        return display_frame
    
    def draw_detection(self, frame, detection):
        """Dibuja la información de detección en el frame"""
        x, y, w, h = detection['bbox']
        
        # Color según persona (conocida/desconocida)
        if detection['person_name'] != "Desconocido" and detection['person_name'] != "Error":
            color = (0, 255, 0)  # Verde para conocidos
            label_color = (0, 200, 0)
        else:
            color = (0, 0, 255)  # Rojo para desconocidos
            label_color = (0, 0, 200)
        
        # Dibujar rectángulo más grueso
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
        
        # Fondo semi-transparente para texto
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y-80), (x+w, y-10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Texto de persona
        cv2.putText(frame, f"Persona: {detection['person_name']}", 
                   (x+10, y-55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Texto de emoción con color
        if detection['emotion']:
            emotion_color = self.emotion_classifier.get_emotion_color(detection['emotion'])
            cv2.putText(frame, f"Emocion: {detection['emotion']}", 
                       (x+10, y-35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, emotion_color, 2)
        
        # Texto de confianza
        if detection['confidence']:
            conf_text = f"Conf: {detection['confidence']:.1%}"
            cv2.putText(frame, conf_text, 
                       (x+10, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def display_frame(self, frame):
        """Muestra el frame en la interfaz"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Escalar imagen manteniendo aspecto
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
    
    def update_info(self, detection):
        """Actualiza la información en el panel derecho"""
        # Información de persona
        self.lbl_person_name.setText(detection['person_name'])
        
        if detection['person_id']:
            # Aquí podrías buscar el email si lo tienes
            self.lbl_person_email.setText("Registrado")
        else:
            self.lbl_person_email.setText("No registrado")
        
        # Información de emoción
        if detection['emotion']:
            self.lbl_emotion.setText(detection['emotion'])
            if detection['confidence']:
                self.lbl_confidence.setText(f"Confianza: {detection['confidence']:.1%}")
                
                # Actualizar barra de confianza
                bar_width = int(detection['confidence'] * self.confidence_frame.width())
                self.confidence_bar.setFixedWidth(max(bar_width, 0))
        else:
            self.lbl_emotion.setText("---")
            self.lbl_confidence.setText("Confianza: ---")
            self.confidence_bar.setFixedWidth(0)
    
    def clear_info(self):
        """Limpia la información mostrada"""
        self.lbl_person_name.setText("---")
        self.lbl_person_email.setText("---")
        self.lbl_emotion.setText("---")
        self.lbl_confidence.setText("Confianza: ---")
        self.confidence_bar.setFixedWidth(0)
    
    def update_stats(self):
        """Actualiza las estadísticas de la sesión"""
        self.lbl_total_detections.setText(f"Detecciones en sesión: {self.session_detections}")
        self.lbl_unique_persons.setText(f"Personas distintas: {len(self.session_persons)}")