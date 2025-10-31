import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g

app = Flask(__name__)
app.secret_key = "aromalux_secret_key"
DATABASE = "usuarios.db"

# -----------------------------------
# FUNCIONES DE BASE DE DATOS
# -----------------------------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Crea las tablas necesarias."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()

        # Tabla usuarios
        c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario TEXT UNIQUE,
                        clave TEXT
                    )''')

        # Tabla perfumes
        c.execute('''CREATE TABLE IF NOT EXISTS perfumes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT,
                        marca TEXT,
                        precio REAL,
                        descripcion TEXT,
                        img TEXT
                    )''')

        # Usuario administrador por defecto
        c.execute("SELECT * FROM usuarios WHERE usuario = ?", ("admin",))
        if not c.fetchone():
            c.execute("INSERT INTO usuarios (usuario, clave) VALUES (?, ?)", ("admin", "1234"))
        conn.commit()

# -----------------------------------
# RUTAS
# -----------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario = request.form["usuario"]
        clave = request.form["clave"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND clave = ?", (usuario, clave))
        user = cursor.fetchone()

        if user:
            return redirect(url_for("home", usuario=usuario))
        else:
            error = "Usuario o contraseña incorrectos"

    return render_template("login.html", error=error)


@app.route("/home")
def home():
    usuario = request.args.get("usuario", "Invitado")
    conn = get_db()
    perfumes = conn.execute("SELECT * FROM perfumes").fetchall()
    return render_template("home.html", usuario=usuario, perfumes=perfumes)


@app.route("/catalogo")
def catalogo():
    conn = get_db()
    perfumes = conn.execute("SELECT * FROM perfumes").fetchall()
    return render_template("catalogo.html", perfumes=perfumes)


@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        nombre = request.form["nombre"]
        marca = request.form["marca"]
        precio = request.form["precio"]
        descripcion = request.form["descripcion"]
        img = request.form.get("img", None)

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO perfumes (nombre, marca, precio, descripcion, img)
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, marca, precio, descripcion, img))
            conn.commit()

            flash("✅ Perfume guardado correctamente", "success")
            return redirect(url_for("home", usuario="admin"))
        except Exception as e:
            flash("❌ Error al guardar perfume: " + str(e), "error")

    return render_template("agregar.html")


@app.route("/eliminar/<int:id>")
def eliminar(id):
    conn = get_db()
    conn.execute("DELETE FROM perfumes WHERE id = ?", (id,))
    conn.commit()
    flash("🗑️ Perfume eliminado correctamente", "success")
    return redirect(url_for("home", usuario="admin"))


@app.route("/logout")
def logout():
    return redirect(url_for("login"))


# -----------------------------------
# EJECUCIÓN
# -----------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
