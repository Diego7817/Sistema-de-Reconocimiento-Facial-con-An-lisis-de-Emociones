# test_models_simple.py
import sys
import os

print("=== TEST SIMPLE DE MODELS ===\n")

# Configurar path
sys.path.insert(0, os.path.abspath('.'))
print(f"Directorio actual: {os.getcwd()}")
print(f"Python path: {sys.path[0]}")

# Intentar importar paso a paso
try:
    print("\n1. Importando sqlalchemy...")
    from sqlalchemy import Column, Integer, String
    print("✅ SQLAlchemy OK")
except Exception as e:
    print(f"❌ Error: {e}")

try:
    print("\n2. Leyendo archivo models.py...")
    with open('src/database/models.py', 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"✅ Archivo leído ({len(content)} bytes)")
        if 'class Persona' in content:
            print("   ✅ Clase Persona encontrada en el archivo")
        else:
            print("   ❌ Clase Persona NO encontrada en el archivo")
except Exception as e:
    print(f"❌ Error: {e}")

try:
    print("\n3. Importando módulo models...")
    import src.database.models as models
    print(f"✅ Módulo importado: {models}")
    print(f"   Contenido del módulo: {dir(models)}")
except Exception as e:
    print(f"❌ Error: {e}")

try:
    print("\n4. Importando Persona específicamente...")
    from src.database.models import Persona
    print(f"✅ Persona importada: {Persona}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50)
input("Presiona Enter para salir...")