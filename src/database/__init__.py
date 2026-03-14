# src/database/__init__.py
"""
Módulo de base de datos
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar usando rutas absolutas
from src.database.models import Base, Persona, Deteccion
from src.database.database_manager import DatabaseManager

# Definir qué se exporta
__all__ = ['Base', 'Persona', 'Deteccion', 'DatabaseManager']

# Para depuración
print(f"✅ Módulo database cargado: {__name__}")
print(f"   Clases disponibles: {[cls for cls in __all__]}")