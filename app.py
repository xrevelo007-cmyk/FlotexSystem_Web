from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import urllib.parse
from datetime import datetime, timedelta
from database import DB_NAME, inicializar_base_datos

app = Flask(__name__)
app.secret_key = "flotex_system_secret_key_secure"

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

inicializar_base_datos()

def actualizar_tablas_bd():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    columnas_cliente = [
        ("direccion", "TEXT"),
        ("contacto_emergencia", "TEXT"),
        ("parentesco_emergencia", "TEXT"),
        ("foto", "TEXT"),
        ("plan", "TEXT"),
        ("fecha_vencimiento", "TEXT")
    ]
    for col, tipo in columnas_cliente:
        try:
            cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            numero_recibo TEXT,
            mes_trabajo TEXT,
            fecha_pago DATE,
            fecha_inicio DATE,
            plan TEXT,
            valor REAL,
            fecha_vencimiento DATE,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

actualizar_tablas_bd()

def calcular_semaforo(fecha_venc_str):
    if not fecha_venc_str:
        return 'rojo', -999, 'Sin fecha'
    try:
        fecha_venc = datetime.strptime(str(fecha_venc_str), '%Y-%m-%d').date()
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

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, cargo FROM staff WHERE usuario = ? AND password = ?", (usuario, password))
            user_data = cursor.fetchone()
            if user_data:
                session["usuario"] = usuario
                session["nombre"] = user_data[1]
                session["cargo"] = user_data[2]
                conn.close()
                return redirect(url_for("dashboard"))
            else:
                conn.close()
                flash("Credenciales incorrectas.", "error")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template("login.html")

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
        telefono = request.form.get("telefono", "").strip()
        cargo = request.form.get("cargo", "Entrenador").strip()
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        if not cedula.isdigit() or len(cedula) != 10:
            flash("La cédula debe tener exactamente 10 dígitos.", "error")
        else:
            try:
                cursor.execute("""
                    INSERT INTO staff (cedula, nombre, telefono, cargo, usuario, password, primer_ingreso)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (cedula, nombre, telefono, cargo, usuario, password))
                conn.commit()
                flash("Miembro de Staff registrado con éxito.", "success")
            except sqlite3.IntegrityError:
                flash("Error: La cédula o usuario ya existe.", "error")
            except Exception as e:
                flash(f"Error al registrar staff: {e}", "error")

    cursor.execute("SELECT id, cedula, nombre, telefono, cargo, usuario FROM staff")
    staff_list = cursor.fetchall()
    conn.close()

    return render_template("staff.html", staff_list=staff_list, nombre=session.get("nombre"))

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
        direccion = request.form.get("direccion", "").strip()
        contacto_emergencia = request.form.get("contacto_emergencia", "").strip()
        parentesco_emergencia = request.form.get("parentesco_emergencia", "").strip()
        
        plan = request.form.get("plan", "Mensual").strip()
        valor_raw = request.form.get("valor", "30.00")
        valor = float(valor_raw) if valor_raw else 30.0
        numero_recibo = request.form.get("numero_recibo", "1001").strip()
        mes_trabajo = request.form.get("mes_trabajo", "").strip()
        fecha_pago = request.form.get("fecha_pago", "").strip()
        fecha_inicio = request.form.get("fecha_inicio", "").strip()
        fecha_vencimiento = request.form.get("fecha_vencimiento", "").strip()

        foto_filename = "default.png"
        file = request.files.get('foto_file')
        if file and file.filename != '':
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            foto_filename = f"{cedula}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))

        if not cedula.isdigit() or len(cedula) != 10:
            flash("La cédula debe contener exactamente 10 dígitos numéricos.", "error")
        else:
            try:
                cursor.execute("""
                    INSERT INTO clientes (cedula, nombre, telefono, direccion, contacto_emergencia, parentesco_emergencia, fecha_vencimiento, estado, plan, foto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Activo', ?, ?)
                """, (cedula, nombre, telefono, direccion, contacto_emergencia, parentesco_emergencia, fecha_vencimiento, plan, foto_filename))
                
                cliente_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO pagos (cliente_id, numero_recibo, mes_trabajo, fecha_pago, fecha_inicio, plan, valor, fecha_vencimiento)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (cliente_id, numero_recibo, mes_trabajo, fecha_pago, fecha_inicio, plan, valor, fecha_vencimiento))

                conn.commit()
                flash("Ficha de cliente y recibo de pago registrados con éxito.", "success")
            except sqlite3.IntegrityError:
                flash("Error: La cédula ya se encuentra registrada.", "error")
            except Exception as e:
                flash(f"Error al registrar: {e}", "error")

    try:
        cursor.execute("SELECT id, cedula, nombre, telefono, direccion, contacto_emergencia, parentesco_emergencia, plan, fecha_vencimiento, estado, foto FROM clientes")
        raw_clientes = cursor.fetchall()
    except Exception:
        raw_clientes = []
    
    try:
        cursor.execute("SELECT MAX(CAST(numero_recibo AS INTEGER)) FROM pagos")
        res_recibo = cursor.fetchone()
        ultimo_recibo = res_recibo[0] if res_recibo else None
        siguiente_recibo = str(int(ultimo_recibo) + 1) if ultimo_recibo else "1001"
    except Exception:
        siguiente_recibo = "1001"

    conn.close()

    clientes_procesados = []
    for c in raw_clientes:
        c_id = c[0]
        cedula = c[1]
        nombre = c[2]
        telefono = c[3]
        direccion = c[4] if len(c) > 4 else ""
        contacto_emergencia = c[5] if len(c) > 5 else ""
        parentesco_emergencia = c[6] if len(c) > 6 else ""
        plan = c[7] if len(c) > 7 else "Mensual"
        fecha_venc = c[8] if len(c) > 8 else ""
        estado = c[9] if len(c) > 9 else "Activo"
        foto = c[10] if len(c) > 10 and c[10] else "default.png"

        color, dias, texto_estado = calcular_semaforo(fecha_venc)
        foto_url = url_for('static', filename=f'uploads/{foto}') if foto and foto != "default.png" else 'https://cdn-icons-png.flaticon.com/512/847/847969.png'
        
        # Formato de WhatsApp para Ecuador (+593)
        tel_clean = ''.join(filter(str.isdigit, str(telefono)))
        if tel_clean.startswith('0'):
            tel_clean = '593' + tel_clean[1:]
        elif not tel_clean.startswith('593') and len(tel_clean) == 9:
            tel_clean = '593' + tel_clean

        # Mensaje amigable según el Semáforo para Planeta Fitness
        if color == 'rojo':
            msg = f"¡Hola {nombre}! 🥊 Te extrañamos en Planeta Fitness. Tu membresía venció el {fecha_venc}. ¡No dejes enfriar el ritmo! Pasa por recepción para renovar y seguir entrenando duro. 💪🚀"
        else:
            msg = f"¡Hola {nombre}! 🏋️‍♂️ Te saluda el equipo de Planeta Fitness. Te recordamos que tu membresía vence el {fecha_venc}. ¡Pasa por recepción para renovar y seguir con todo! 💪🔥"

        ws_url = f"https://api.whatsapp.com/send?phone={tel_clean}&text={urllib.parse.quote(msg)}"

        clientes_procesados.append({
            'id': c_id,
            'cedula': cedula,
            'nombre': nombre,
            'telefono': telefono,
            'direccion': direccion,
            'contacto_emergencia': contacto_emergencia,
            'parentesco_emergencia': parentesco_emergencia,
            'plan': plan,
            'fecha_vencimiento': fecha_venc,
            'foto': foto_url,
            'color': color,
            'dias_restantes': dias,
            'texto_estado': texto_estado,
            'ws_url': ws_url
        })

    return render_template("clientes.html", clientes_list=clientes_procesados, nombre=session.get("nombre"), siguiente_recibo=siguiente_recibo)

# --- RENOVACIÓN / PAGO DE MENSUALIDAD ---
@app.route("/clientes/renovar/<int:cliente_id>", methods=["POST"])
def renovar_cliente(cliente_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    numero_recibo = request.form.get("numero_recibo", "").strip()
    mes_trabajo = request.form.get("mes_trabajo", "").strip()
    fecha_pago = request.form.get("fecha_pago", "").strip()
    fecha_inicio = request.form.get("fecha_inicio", "").strip()
    plan = request.form.get("nuevo_plan", "").strip()
    valor_raw = request.form.get("valor", "30.00")
    valor = float(valor_raw) if valor_raw else 30.0
    fecha_vencimiento = request.form.get("fecha_vencimiento", "").strip()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO pagos (cliente_id, numero_recibo, mes_trabajo, fecha_pago, fecha_inicio, plan, valor, fecha_vencimiento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cliente_id, numero_recibo, mes_trabajo, fecha_pago, fecha_inicio, plan, valor, fecha_vencimiento))

        cursor.execute("""
            UPDATE clientes 
            SET fecha_vencimiento = ?, plan = ? 
            WHERE id = ?
        """, (fecha_vencimiento, plan, cliente_id))

        conn.commit()
        flash(f"¡Recibo #{numero_recibo} procesado y membresía renovada con éxito!", "success")
    except Exception as e:
        flash(f"Error al procesar el pago: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for("clientes"))

@app.route("/clientes/eliminar/<int:cliente_id>")
def eliminar_cliente(cliente_id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()
    flash("Cliente eliminado.", "success")
    return redirect(url_for("clientes"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)