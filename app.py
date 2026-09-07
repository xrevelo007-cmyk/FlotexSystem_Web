from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from database import DB_NAME, inicializar_base_datos

app = Flask(__name__)
app.secret_key = "flotex_system_secret_key_secure"

# Inicializar Base de Datos
inicializar_base_datos()

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
                flash("Usuario o contraseña incorrectos.", "error")

        except Exception as e:
            flash(f"Error en el servidor: {e}", "error")

    return render_template("login.html")

# --- RUTA DASHBOARD ---
@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", nombre=session.get("nombre"), cargo=session.get("cargo"))

# --- MÓDULO DE STAFF ---
@app.route("/staff", methods=["GET", "POST"])
def staff():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        nombre = request.form.get("nombre", "").strip()
        cargo = request.form.get("cargo", "").strip()
        telefono = request.form.get("telefono", "").strip()
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        # Validación estricta de 10 dígitos numéricos
        if not cedula.isdigit() or len(cedula) != 10:
            flash("La cédula debe contener exactamente 10 dígitos numéricos.", "error")
        elif telefono and (not telefono.isdigit() or len(telefono) != 10):
            flash("El teléfono debe contener exactamente 10 dígitos numéricos.", "error")
        else:
            try:
                cursor.execute("""
                    INSERT INTO staff (cedula, nombre, cargo, telefono, usuario, password)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (cedula, nombre, cargo, telefono, usuario, password))
                conn.commit()
                flash("Usuario creado exitosamente.", "success")
            except sqlite3.IntegrityError:
                flash("Error: La cédula o el usuario ya existen.", "error")
            except Exception as e:
                flash(f"Error al guardar: {e}", "error")

    cursor.execute("SELECT id, cedula, nombre, cargo, telefono, usuario, estado FROM staff")
    lista_staff = cursor.fetchall()
    conn.close()

    return render_template("staff.html", staff_members=lista_staff, nombre=session.get("nombre"))

# --- ELIMINAR STAFF ---
@app.route("/staff/eliminar/<int:staff_id>")
def eliminar_staff(staff_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Evitar eliminar al creador
    cursor.execute("SELECT cedula FROM staff WHERE id = ?", (staff_id,))
    target = cursor.fetchone()
    if target and target[0] == "1722207287":
        flash("No es posible eliminar la cuenta principal del creador.", "error")
    else:
        cursor.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
        conn.commit()
        flash("Usuario eliminado correctamente.", "success")
        
    conn.close()
    return redirect(url_for("staff"))

# --- CERRAR SESIÓN ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)