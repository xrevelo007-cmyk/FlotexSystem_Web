import sqlite3

# Ruta segura para base de datos
DB_NAME = 'gym_sistema.db'

def conectar_db():
    return sqlite3.connect(DB_NAME)

def inicializar_base_datos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    # 1. Tabla de Usuarios / Staff
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            cargo TEXT NOT NULL,
            telefono TEXT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            primer_ingreso INTEGER DEFAULT 1,
            estado TEXT DEFAULT 'Activo'
        )
    """)
    
    # Insertar administrador por defecto si no existe
    cursor.execute("SELECT COUNT(*) FROM staff")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO staff (cedula, nombre, cargo, telefono, usuario, password, primer_ingreso)
            VALUES ('1722207287', 'Xavier Revelo', 'Administrador', '0000000000', '1722207287', 'Ligacampeon24', 1)
        """)
        conexion.commit()

    # 2. Tabla de Clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            cedula TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            edad INTEGER,
            direccion TEXT,
            telefono TEXT,
            emergencia TEXT,
            medico TEXT,
            ruta_foto TEXT,
            plan TEXT,
            precio_plan REAL,
            fecha_inicio TEXT,
            fecha_vencimiento TEXT,
            grupo_id TEXT DEFAULT ''
        )
    """)

    # 3. Tabla de Inventario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    # 4. Tabla de Ventas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            nombre_producto TEXT,
            cantidad INTEGER,
            total REAL,
            efectivo REAL,
            transferencia REAL,
            usuario TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conexion.commit()
    conexion.close()

# Ejecutar inicialización al importar
inicializar_base_datos()