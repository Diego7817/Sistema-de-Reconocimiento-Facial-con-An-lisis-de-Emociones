# verificar_datos.py
import sqlite3
import os

print("=== VERIFICANDO BASE DE DATOS ===\n")

db_path = 'facial_recognition.db'

if os.path.exists(db_path):
    print(f"✅ Base de datos encontrada: {db_path}")
    print(f"📊 Tamaño: {os.path.getsize(db_path)} bytes")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\n📋 Tablas encontradas: {[t[0] for t in tables]}")
    
    # Verificar personas
    cursor.execute("SELECT COUNT(*) FROM personas;")
    count_personas = cursor.fetchone()[0]
    print(f"\n👥 Personas registradas: {count_personas}")
    
    if count_personas > 0:
        cursor.execute("SELECT id, nombre, apellido, email FROM personas;")
        personas = cursor.fetchall()
        for p in personas:
            print(f"   - ID {p[0]}: {p[1]} {p[2]} ({p[3]})")
    
    # Verificar detecciones
    cursor.execute("SELECT COUNT(*) FROM detecciones;")
    count_detecciones = cursor.fetchone()[0]
    print(f"\n📝 Detecciones registradas: {count_detecciones}")
    
    if count_detecciones > 0:
        cursor.execute("""
            SELECT d.id, p.nombre, p.apellido, d.emocion_detectada, 
                   d.nivel_confianza, d.timestamp 
            FROM detecciones d
            JOIN personas p ON d.persona_id = p.id
            ORDER BY d.timestamp DESC LIMIT 5;
        """)
        detecciones = cursor.fetchall()
        for d in detecciones:
            print(f"   - {d[5]}: {d[1]} {d[2]} - {d[3]} ({d[4]:.1%})")
    
    conn.close()
else:
    print(f"❌ Base de datos NO encontrada: {db_path}")

print("\n" + "="*50)