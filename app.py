from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
from database import DB_NAME, inicializar_base_datos

app = Flask(__name__)
app.secret_key = "flotex_system_secret_key_secure"

# Inicializar Base de Datos
inicializar_base_datos()

# Asegurar columna 'foto' en la tabla clientes
def actualizar_tabla_clientes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE clientes ADD COLUMN foto TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass # La columna ya existe
    conn.close()

actualizar_tabla_clientes()

def calcular_semaforo(fecha_venc_str):
    if not fecha_venc_str:
        return 'rojo', -999, 'Sin fecha'
    try:
        fecha_venc = datetime.strptime(fecha_venc_str, '%Y-%m-%d').date()
        hoy = datetime.now().date()
        dias_restantes = (fecha_venc - hoy).days
        
        if dias_restantes > 3:
            return 'verde', dias_restantes, 'AL DÍA'
        elif 0 <= dias_restantes <= 3:
            return 'amarillo', dias_restantes, 'POR VENCER'
        else:
            return 'rojo', dias_restantes, 'VENCIDO / MOROSO'
    except Exception:
        return 'rojo', 0, 'ERROR FECHA'

# --- RUTA LOGIN ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        if not usuario or not password:
            flash("Por favor ingresa tu usuario y contraseña.", "error")
            return redirect(url_for("login"))

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombre, cargo, primer_ingreso 
                FROM staff 
                WHERE usuario = ? AND password = ?
            """, (usuario, password))
            user_data = cursor.fetchone()

            if user_data:
                user_id, nombre, cargo, primer_ingreso = user_data
                session["usuario"] = usuario
                session["nombre"] = nombre
                session["cargo"] = cargo

                if primer_ingreso == 1 and usuario == "1722207287":
                    cursor.execute("UPDATE staff SET primer_ingreso = 0 WHERE id = ?", (user_id,))
                    conn.commit()
                    flash("¡Bienvenido Creador Xavier Revelo! Instancia configurada con éxito.", "success")
                else:
                    flash(f"Sesión iniciada correctamente. ¡Hola, {nombre}!", "success")
                
                conn.close()
                return redirect(url_for("dashboard"))
            else:
                conn.close()
                flash("Credenciales incorrectas. Verifica tu usuario y contraseña.", "error")
        except Exception as e:
            flash(f"Error en el sistema: {e}", "error")

    return render_template("login.html")

# --- DASHBOARD ---
@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", nombre=session.get("nombre"), cargo=session.get("cargo"))

# --- MÓDULO DE CLIENTES ---
@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        plan = request.form.get("plan", "").strip()
        fecha_vencimiento = request.form.get("fecha_vencimiento", "").strip()
        foto = request.form.get("foto", "").strip()

        if not cedula.isdigit() or len(cedula) != 10:
            flash("La cédula del cliente debe contener exactamente 10 dígitos numéricos.", "error")
        elif telefono and (not telefono.isdigit() or len(telefono) != 10):
            flash("El teléfono debe contener exactamente 10 dígitos numéricos.", "error")
        else:
            try:
                cursor.execute("""
                    INSERT INTO clientes (cedula, nombre, telefono, plan, fecha_vencimiento, estado, foto)
                    VALUES (?, ?, ?, ?, ?, 'Activo', ?)
                """, (cedula, nombre, telefono, plan, fecha_vencimiento, foto))
                conn.commit()
                flash("Cliente registrado exitosamente.", "success")
            except sqlite3.IntegrityError:
                flash("Error: La cédula de este cliente ya se encuentra registrada.", "error")
            except Exception as e:
                flash(f"Error al guardar cliente: {e}", "error")

    cursor.execute("SELECT id, cedula, nombre, telefono, plan, fecha_vencimiento, estado, foto FROM clientes")
    raw_clientes = cursor.fetchall()
    conn.close()

    clientes_procesados = []
    for c in raw_clientes:
        c_id, cedula, nombre, telefono, plan, fecha_venc, estado, foto = c
        color, dias, texto_estado = calcular_semaforo(fecha_venc)
        clientes_procesados.append({
            'id': c_id,
            'cedula': cedula,
            'nombre': nombre,
            'telefono': telefono,
            'plan': plan,
            'fecha_vencimiento': fecha_venc,
            'foto': foto if foto else 'https://cdn-icons-png.flaticon.com/512/847/847969.png',
            'color': color,
            'dias_restantes': dias,
            'texto_estado': texto_estado
        })

    return render_template("clientes.html", clientes_list=clientes_procesados, nombre=session.get("nombre"))

# --- ELIMINAR CLIENTE ---
@app.route("/clientes/eliminar/<int:cliente_id>")
def eliminar_cliente(cliente_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()
    
    flash("Cliente eliminado correctamente.", "success")
    return redirect(url_for("clientes"))

# --- CERRAR SESIÓN ---
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)