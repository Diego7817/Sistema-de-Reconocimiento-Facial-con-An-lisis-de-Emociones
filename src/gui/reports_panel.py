# src/gui/reports_panel.py
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QFileDialog,
                             QMessageBox, QDateEdit)
from PyQt5.QtCore import Qt, QDate
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ReportsPanel(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
        
    def init_ui(self):
        """Inicializa la interfaz del panel de reportes"""
        layout = QVBoxLayout(self)
        
        # Controles de filtro
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout()
        
        # Selector de persona
        self.person_combo = QComboBox()
        self.person_combo.addItem("Todas las personas", None)
        self.person_combo.currentIndexChanged.connect(self.refresh_data)
        filter_layout.addWidget(QLabel("Persona:"))
        filter_layout.addWidget(self.person_combo)
        
        # Selector de fechas
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        
        filter_layout.addWidget(QLabel("Desde:"))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("Hasta:"))
        filter_layout.addWidget(self.end_date)
        
        # Botón actualizar
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        filter_layout.addWidget(self.btn_refresh)
        
        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Área de gráficos y tablas
        content_layout = QHBoxLayout()
        
        # Panel izquierdo - Gráficos
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Gráfico de emociones
        graph_group = QGroupBox("Distribución de Emociones")
        graph_layout = QVBoxLayout()
        
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        graph_layout.addWidget(self.canvas)
        graph_group.setLayout(graph_layout)
        left_layout.addWidget(graph_group)
        
        # Estadísticas generales
        stats_group = QGroupBox("Estadísticas Generales")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QLabel()
        self.stats_text.setAlignment(Qt.AlignTop)
        self.stats_text.setWordWrap(True)
        self.stats_text.setStyleSheet("font-size: 12px; padding: 10px;")
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        left_layout.addWidget(stats_group)
        
        content_layout.addWidget(left_panel, 1)
        
        # Panel derecho - Tabla de historial
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        history_group = QGroupBox("Historial de Detecciones")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(
            ["Fecha", "Persona", "Emoción", "Confianza", "Hora"]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        right_layout.addWidget(history_group)
        
        # Botones de exportación
        export_layout = QHBoxLayout()
        
        self.btn_export_csv = QPushButton("Exportar a CSV")
        self.btn_export_csv.clicked.connect(self.export_to_csv)
        self.btn_export_csv.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        self.btn_export_graph = QPushButton("Guardar Gráfico")
        self.btn_export_graph.clicked.connect(self.save_graph)
        self.btn_export_graph.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        
        export_layout.addWidget(self.btn_export_csv)
        export_layout.addWidget(self.btn_export_graph)
        export_layout.addStretch()
        
        right_layout.addLayout(export_layout)
        
        content_layout.addWidget(right_panel, 1)
        layout.addLayout(content_layout)
        
        # Cargar datos iniciales
        self.load_personas()
        self.refresh_data()
    
    def load_personas(self):
        """Carga la lista de personas en el combo box"""
        try:
            personas = self.db_manager.get_all_personas()
            self.person_combo.clear()
            self.person_combo.addItem("Todas las personas", None)
            
            for p in personas:
                self.person_combo.addItem(
                    f"{p['nombre']} {p['apellido']}",
                    p['id']
                )
            logger.info(f"Cargadas {len(personas)} personas en combo box")
        except Exception as e:
            logger.error(f"Error cargando personas: {e}")
    
    def refresh_data(self):
        """Actualiza todos los datos mostrados"""
        try:
            # Obtener filtros
            persona_id = self.person_combo.currentData()
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            logger.info(f"Actualizando reportes: persona={persona_id}, fechas={start_date} a {end_date}")
            
            # Obtener todas las detecciones
            todas_detecciones = []
            
            if persona_id:
                # Detecciones de una persona específica
                detecciones = self.db_manager.get_detecciones_by_persona(persona_id)
                todas_detecciones.extend(detecciones)
            else:
                # Detecciones de todas las personas
                personas = self.db_manager.get_all_personas()
                for p in personas:
                    detecciones = self.db_manager.get_detecciones_by_persona(p['id'])
                    todas_detecciones.extend(detecciones)
            
            # Filtrar por fecha
            detecciones_filtradas = [
                d for d in todas_detecciones 
                if start_date <= d['timestamp'].date() <= end_date
            ]
            
            logger.info(f"Encontradas {len(detecciones_filtradas)} detecciones en el rango")
            
            # Actualizar tabla
            self.update_table(detecciones_filtradas)
            
            # Actualizar gráfico
            self.update_graph(detecciones_filtradas)
            
            # Actualizar estadísticas
            self.update_stats(detecciones_filtradas)
            
        except Exception as e:
            logger.error(f"Error actualizando datos: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"No se pudieron actualizar los datos: {str(e)}")
    
    def update_table(self, detecciones):
        """Actualiza la tabla con las detecciones"""
        self.history_table.setRowCount(len(detecciones))
        
        for i, det in enumerate(detecciones):
            # Fecha
            date_item = QTableWidgetItem(det['timestamp'].strftime("%Y-%m-%d"))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 0, date_item)
            
            # Persona
            person_item = QTableWidgetItem(det.get('persona_nombre', 'Desconocido'))
            person_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 1, person_item)
            
            # Emoción
            emotion_item = QTableWidgetItem(det['emocion'])
            emotion_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 2, emotion_item)
            
            # Confianza
            confidence_item = QTableWidgetItem(f"{det['confianza']:.1%}")
            confidence_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 3, confidence_item)
            
            # Hora
            time_item = QTableWidgetItem(det['timestamp'].strftime("%H:%M:%S"))
            time_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 4, time_item)
    
    def update_graph(self, detecciones):
        """Actualiza el gráfico de distribución de emociones"""
        # Limpiar figura
        self.figure.clear()
        
        if not detecciones:
            # Mostrar mensaje de "sin datos"
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No hay datos para mostrar', 
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes,
                   fontsize=14)
            ax.set_title('Distribución de Emociones')
            self.canvas.draw()
            return
        
        # Contar emociones
        emotion_counts = {}
        for det in detecciones:
            emotion = det['emocion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Crear gráfico de pastel
        ax = self.figure.add_subplot(111)
        
        emotions = list(emotion_counts.keys())
        counts = list(emotion_counts.values())
        
        # Colores para cada emoción
        colors = {
            'Felicidad': '#2ecc71',
            'Tristeza': '#3498db',
            'Enojo': '#e74c3c',
            'Sorpresa': '#f1c40f',
            'Miedo': '#9b59b6',
            'Disgusto': '#e67e22',
            'Neutral': '#95a5a6'
        }
        
        color_list = [colors.get(e, '#34495e') for e in emotions]
        
        # Crear gráfico
        wedges, texts, autotexts = ax.pie(
            counts, 
            labels=emotions, 
            colors=color_list, 
            autopct='%1.1f%%',
            textprops={'fontsize': 10}
        )
        
        # Mejorar formato de porcentajes
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Distribución de Emociones Detectadas', fontsize=12, fontweight='bold')
        
        self.canvas.draw()
    
    def update_stats(self, detecciones):
        """Actualiza las estadísticas generales"""
        if not detecciones:
            self.stats_text.setText("No hay datos para mostrar en el período seleccionado.\n\n"
                                   "📝 Sugerencias:\n"
                                   "• Amplíe el rango de fechas\n"
                                   "• Registre más personas\n"
                                   "• Realice detecciones en el panel de Detección")
            return
        
        # Calcular estadísticas
        total_detecciones = len(detecciones)
        
        # Personas únicas
        personas_unicas = len(set(d.get('persona_nombre', 'Desconocido') for d in detecciones))
        
        # Emoción más común
        emotion_counts = {}
        for det in detecciones:
            emotion_counts[det['emocion']] = emotion_counts.get(det['emocion'], 0) + 1
        
        most_common_emotion = max(emotion_counts.items(), key=lambda x: x[1])
        
        # Confianza promedio
        avg_confidence = sum(d['confianza'] for d in detecciones) / total_detecciones
        
        # Rango de fechas
        fechas = [d['timestamp'].date() for d in detecciones]
        fecha_min = min(fechas)
        fecha_max = max(fechas)
        
        stats_text = f"""
📊 **ESTADÍSTICAS GENERALES**

• **Total de detecciones:** {total_detecciones}
• **Personas distintas:** {personas_unicas}
• **Emoción más frecuente:** {most_common_emotion[0]} ({most_common_emotion[1]} veces, {most_common_emotion[1]/total_detecciones*100:.1f}%)
• **Confianza promedio:** {avg_confidence:.1%}
• **Período analizado:** {fecha_min} al {fecha_max}
• **Días con actividad:** {(fecha_max - fecha_min).days + 1} días
        """
        
        self.stats_text.setText(stats_text)
    
    def export_to_csv(self):
        """Exporta los datos a CSV"""
        try:
            # Verificar si hay datos
            if self.history_table.rowCount() == 0:
                QMessageBox.warning(self, "Sin datos", "No hay datos para exportar")
                return
            
            # Seleccionar ubicación
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar CSV",
                f"reporte_emociones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not filename:
                return
            
            # Obtener datos de la tabla
            data = []
            headers = ["Fecha", "Persona", "Emoción", "Confianza", "Hora"]
            data.append(headers)
            
            for row in range(self.history_table.rowCount()):
                row_data = []
                for col in range(self.history_table.columnCount()):
                    item = self.history_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # Crear DataFrame y guardar
            df = pd.DataFrame(data[1:], columns=data[0])
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            QMessageBox.information(
                self,
                "Éxito",
                f"✅ Datos exportados correctamente a:\n{filename}"
            )
            
        except Exception as e:
            logger.error(f"Error exportando a CSV: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo exportar: {str(e)}"
            )
    
    def save_graph(self):
        """Guarda el gráfico como imagen"""
        try:
            # Seleccionar ubicación
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Gráfico",
                f"grafico_emociones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG Files (*.png);;JPG Files (*.jpg)"
            )
            
            if filename:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"✅ Gráfico guardado correctamente en:\n{filename}"
                )
                
        except Exception as e:
            logger.error(f"Error guardando gráfico: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el gráfico: {str(e)}"
            )