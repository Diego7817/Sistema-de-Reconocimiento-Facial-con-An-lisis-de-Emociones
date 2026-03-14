# src/gui/register_panel.py
import cv2
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QGroupBox, QFormLayout,
                             QMessageBox, QProgressBar)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from src.face_recognition.face_encoder import FaceEncoder
from src.face_recognition.face_recognizer import FaceRecognizer
import logging

logger = logging.getLogger(__name__)

class RegisterPanel(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.face_encoder = FaceEncoder()
        self.face_recognizer = FaceRecognizer(db_manager)  # ¡AGREGADO!
        self.camera = None
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_frame)
        self.captured_embeddings = []
        self.current_quality = {}
        self.init_ui()
        
    def init_ui(self):
        """Inicializa la interfaz del panel de registro"""
        layout = QHBoxLayout(self)
        
        # Panel izquierdo - Formulario
        form_panel = QWidget()
        form_layout = QVBoxLayout(form_panel)
        
        # Grupo de datos personales
        personal_group = QGroupBox("Datos Personales")
        personal_form = QFormLayout()
        
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ingrese nombre")
        personal_form.addRow("Nombre:", self.input_nombre)
        
        self.input_apellido = QLineEdit()
        self.input_apellido.setPlaceholderText("Ingrese apellido")
        personal_form.addRow("Apellido:", self.input_apellido)
        
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Ingrese email")
        personal_form.addRow("Email:", self.input_email)
        
        personal_group.setLayout(personal_form)
        form_layout.addWidget(personal_group)
        
        # Indicador de calidad
        quality_group = QGroupBox("Calidad de Captura")
        quality_layout = QVBoxLayout()
        
        self.quality_label = QLabel("Esperando captura...")
        self.quality_bar = QProgressBar()
        self.quality_bar.setRange(0, 100)
        quality_layout.addWidget(self.quality_label)
        quality_layout.addWidget(self.quality_bar)
        quality_group.setLayout(quality_layout)
        form_layout.addWidget(quality_group)
        
        # Contador de capturas
        self.capture_count_label = QLabel("Capturas: 0/5")
        self.capture_count_label.setAlignment(Qt.AlignCenter)
        self.capture_count_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        form_layout.addWidget(self.capture_count_label)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.btn_capture = QPushButton("Capturar Rostro")
        self.btn_capture.setEnabled(False)
        self.btn_capture.clicked.connect(self.capture_face)
        self.btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        
        self.btn_register = QPushButton("Registrar Persona")
        self.btn_register.setEnabled(False)
        self.btn_register.clicked.connect(self.register_person)
        self.btn_register.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        
        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.clicked.connect(self.clear_form)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        
        btn_layout.addWidget(self.btn_capture)
        btn_layout.addWidget(self.btn_register)
        btn_layout.addWidget(self.btn_clear)
        
        form_layout.addLayout(btn_layout)
        form_layout.addStretch()
        
        # Panel derecho - Vista de cámara
        camera_panel = QWidget()
        camera_layout = QVBoxLayout(camera_panel)
        
        camera_group = QGroupBox("Vista Previa de Cámara")
        camera_view_layout = QVBoxLayout()
        
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("border: 2px solid #bdc3c7; border-radius: 5px; background-color: #000;")
        camera_view_layout.addWidget(self.camera_label)
        
        # Botón de control de cámara
        self.btn_toggle_camera = QPushButton("Iniciar Cámara")
        self.btn_toggle_camera.clicked.connect(self.toggle_camera)
        self.btn_toggle_camera.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        camera_view_layout.addWidget(self.btn_toggle_camera)
        
        camera_group.setLayout(camera_view_layout)
        camera_layout.addWidget(camera_group)
        
        # Agregar paneles al layout principal
        layout.addWidget(form_panel, 1)
        layout.addWidget(camera_panel, 2)
        
    def toggle_camera(self):
        """Inicia o detiene la cámara"""
        if self.camera is None:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """Inicia la captura de cámara"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                QMessageBox.warning(self, "Error", "No se pudo abrir la cámara")
                return
            
            self.camera_timer.start(30)  # 30 ms ≈ 33 fps
            self.btn_toggle_camera.setText("Detener Cámara")
            self.btn_capture.setEnabled(True)
            logger.info("Cámara iniciada")
            
        except Exception as e:
            logger.error(f"Error al iniciar cámara: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo iniciar la cámara: {str(e)}")
    
    def stop_camera(self):
        """Detiene la captura de cámara"""
        if self.camera_timer.isActive():
            self.camera_timer.stop()
        
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        
        self.camera_label.clear()
        self.btn_toggle_camera.setText("Iniciar Cámara")
        self.btn_capture.setEnabled(False)
        logger.info("Cámara detenida")
    
    def update_frame(self):
        """Actualiza el frame de la cámara"""
        if self.camera is None:
            return
        
        ret, frame = self.camera.read()
        if ret:
            # Analizar calidad del rostro
            quality = self.face_encoder.validate_face_quality(frame)
            self.current_quality = quality
            
            # Actualizar indicadores de calidad
            if quality['face_detected']:
                quality_score = min(100, int(quality['sharpness'] / 2))
                self.quality_bar.setValue(quality_score)
                
                if quality['is_good_quality']:
                    self.quality_label.setText("✓ Buena calidad")
                    self.quality_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    issues = []
                    if quality['sharpness'] <= 80:
                        issues.append("poca nitidez")
                    if quality['brightness'] <= 40 or quality['brightness'] >= 220:
                        issues.append("iluminación incorrecta")
                    
                    self.quality_label.setText(f"⚠ Calidad mejorable: {', '.join(issues)}")
                    self.quality_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.quality_bar.setValue(0)
                self.quality_label.setText("✗ No se detecta rostro")
                self.quality_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Mostrar frame
            self.display_frame(frame)
    
    def display_frame(self, frame):
        """Muestra un frame en la interfaz"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Escalar imagen manteniendo aspecto
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled_pixmap)
    
    def capture_face(self):
        """Captura el rostro actual"""
        if self.camera is None:
            return
        
        ret, frame = self.camera.read()
        if not ret:
            return
        
        # Verificar calidad
        if not self.current_quality.get('is_good_quality', False):
            QMessageBox.warning(
                self,
                "Calidad Insuficiente",
                "La calidad de la imagen no es óptima. Ajuste la iluminación o posición."
            )
            return
        
        # Extraer embedding
        embedding = self.face_encoder.extract_face_encoding(frame)
        
        if embedding is not None:
            self.captured_embeddings.append(embedding)
            count = len(self.captured_embeddings)
            self.capture_count_label.setText(f"Capturas: {count}/5")
            
            if count >= 5:
                self.btn_capture.setEnabled(False)
                self.check_ready_for_registration()
            
            logger.info(f"Rostro capturado {count}/5")
            QMessageBox.information(
                self,
                "Captura Exitosa",
                f"Rostro capturado correctamente ({count}/5)"
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo detectar un rostro en la imagen"
            )
    
    def check_ready_for_registration(self):
        """Verifica si está listo para registrar"""
        if (len(self.captured_embeddings) >= 3 and
            self.input_nombre.text() and
            self.input_apellido.text() and
            self.input_email.text()):
            self.btn_register.setEnabled(True)
        else:
            self.btn_register.setEnabled(False)
    
    def register_person(self):
        """Registra una nueva persona"""
        # Validar campos
        if not all([self.input_nombre.text(), self.input_apellido.text(), self.input_email.text()]):
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return
        
        if len(self.captured_embeddings) < 3:
            QMessageBox.warning(self, "Error", "Debe capturar al menos 3 rostros")
            return
        
        # Calcular embedding promedio
        avg_embedding = np.mean(self.captured_embeddings, axis=0)
        
        # Registrar en base de datos
        success, message = self.face_recognizer.add_new_face(
            self.input_nombre.text(),
            self.input_apellido.text(),
            self.input_email.text(),
            avg_embedding
        )
        
        if success:
            QMessageBox.information(self, "Éxito", "Persona registrada correctamente")
            self.clear_form()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo registrar: {message}")
    
    def clear_form(self):
        """Limpia el formulario"""
        self.input_nombre.clear()
        self.input_apellido.clear()
        self.input_email.clear()
        self.captured_embeddings = []
        self.capture_count_label.setText("Capturas: 0/5")
        self.btn_capture.setEnabled(True)
        self.btn_register.setEnabled(False)