import sqlite3

DB_NAME = "gym_sistema.db"

def inicializar_base_datos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabla Staff
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            cargo TEXT NOT NULL,
            telefono TEXT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            estado TEXT DEFAULT 'Activo',
            primer_ingreso INTEGER DEFAULT 1
        )
    """)
    
    # Usuario Creador por defecto (Xavier Revelo)
    cursor.execute("""
        INSERT OR IGNORE INTO staff (cedula, nombre, cargo, telefono, usuario, password, primer_ingreso)
        VALUES ('1722207287', 'Xavier Revelo', 'Administrador', '0990000000', '1722207287', '1722207287', 1)
    """)

    # 2. Tabla Clientes (Estructura base para el siguiente módulo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            telefono TEXT,
            plan TEXT,
            fecha_vencimiento TEXT,
            estado TEXT DEFAULT 'Activo'
        )
    """)

    # 3. Tabla Inventario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    # 4. Tabla Ventas / Caja
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            metodo_pago TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    inicializar_base_datos()
    print("Base de datos e infraestructura inicializadas correctamente.")