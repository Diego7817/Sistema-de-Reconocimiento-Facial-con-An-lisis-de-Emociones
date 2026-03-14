# src/gui/__init__.py
"""
Módulo de interfaz gráfica
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.gui.main_window import MainWindow
from src.gui.register_panel import RegisterPanel
from src.gui.detection_panel import DetectionPanel
from src.gui.reports_panel import ReportsPanel

__all__ = ['MainWindow', 'RegisterPanel', 'DetectionPanel', 'ReportsPanel']