# src/gui/main_window.py
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QMessageBox,
                             QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .register_panel import RegisterPanel
from .detection_panel import DetectionPanel
from .reports_panel import ReportsPanel
import logging

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario principal"""
        self.setWindowTitle("Sistema de Reconocimiento Facial con Análisis de Emociones")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barra de título
        title_label = QLabel("Sistema de Reconocimiento Facial")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # Barra de navegación
        nav_layout = QHBoxLayout()
        
        self.btn_register = QPushButton("Registro")
        self.btn_detection = QPushButton("Detección")
        self.btn_reports = QPushButton("Reportes")
        
        # Estilo de botones
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:checked {
                background-color: #2c3e50;
            }
        """
        
        for btn in [self.btn_register, self.btn_detection, self.btn_reports]:
            btn.setStyleSheet(button_style)
            btn.setCheckable(True)
            nav_layout.addWidget(btn)
        
        # Botón de salir
        self.btn_exit = QPushButton("Salir")
        self.btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        nav_layout.addWidget(self.btn_exit)
        
        main_layout.addLayout(nav_layout)
        
        # Stacked widget para los diferentes paneles
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Crear paneles
        self.register_panel = RegisterPanel(self.db_manager)
        self.detection_panel = DetectionPanel(self.db_manager)
        self.reports_panel = ReportsPanel(self.db_manager)
        
        # Agregar paneles al stacked widget
        self.stacked_widget.addWidget(self.register_panel)
        self.stacked_widget.addWidget(self.detection_panel)
        self.stacked_widget.addWidget(self.reports_panel)
        
        # Conectar señales
        self.btn_register.clicked.connect(lambda: self.switch_panel(0))
        self.btn_detection.clicked.connect(lambda: self.switch_panel(1))
        self.btn_reports.clicked.connect(lambda: self.switch_panel(2))
        self.btn_exit.clicked.connect(self.close_application)
        
        # ==== BARRA DE ESTADO - AHORA ANTES DE USARLA ====
        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        # Mostrar panel de detección por defecto
        self.btn_detection.setChecked(True)
        self.switch_panel(1)
        
    def switch_panel(self, index):
        """Cambia entre los diferentes paneles"""
        # Actualizar estado de botones
        self.btn_register.setChecked(index == 0)
        self.btn_detection.setChecked(index == 1)
        self.btn_reports.setChecked(index == 2)
        
        # Detener cámara si está activa en otros paneles
        if index != 1:  # Si no es el panel de detección
            if hasattr(self, 'detection_panel'):
                self.detection_panel.stop_detection()
        
        # Cambiar panel
        self.stacked_widget.setCurrentIndex(index)
        
        # Actualizar barra de estado
        panel_names = ["Registro de Personas", "Detección en Tiempo Real", "Reportes y Estadísticas"]
        self.status_label.setText(f"Panel actual: {panel_names[index]}")
        
        # Actualizar datos si es necesario
        if index == 2:  # Panel de reportes
            if hasattr(self, 'reports_panel'):
                self.reports_panel.refresh_data()
    
    def close_application(self):
        """Cierra la aplicación de manera segura"""
        reply = QMessageBox.question(
            self, 'Confirmar salida',
            '¿Está seguro que desea salir?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Detener cámaras
            if hasattr(self, 'detection_panel'):
                self.detection_panel.stop_detection()
            if hasattr(self, 'register_panel'):
                if hasattr(self.register_panel, 'stop_camera'):
                    self.register_panel.stop_camera()
            
            # Cerrar aplicación
            QApplication.quit()
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana"""
        self.close_application()
        event.accept()