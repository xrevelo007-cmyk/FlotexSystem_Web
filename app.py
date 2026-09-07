from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from database import DB_NAME, inicializar_base_datos

app = Flask(__name__)
app.secret_key = "flotex_system_secret_key_secure"

# Inicializar BD al arrancar la app
inicializar_base_datos()

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

@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", nombre=session.get("nombre"), cargo=session.get("cargo"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)