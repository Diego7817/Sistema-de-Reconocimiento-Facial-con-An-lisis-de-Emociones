# main.py
import sys
import os
import logging

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('facial_recognition.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Iniciando aplicación...")
        
        # Importar módulos necesarios
        from PyQt5.QtWidgets import QApplication
        from src.database import DatabaseManager
        from src.gui import MainWindow
        
        # Inicializar Qt
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Inicializar base de datos
        logger.info("Inicializando base de datos...")
        db_manager = DatabaseManager()
        
        # Crear ventana principal
        logger.info("Creando ventana principal...")
        window = MainWindow(db_manager)
        window.show()
        
        logger.info("Aplicación iniciada correctamente")
        
        # Ejecutar aplicación
        sys.exit(app.exec_())
        
    except ImportError as e:
        logger.error(f"Error de importación: {e}")
        print(f"\n❌ Error de importación: {e}")
        print("\nVerifica que todas las dependencias están instaladas:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error en main: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()