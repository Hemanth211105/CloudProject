from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "mysecretkey"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect("cloud.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            filename TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def do_signup():
    username = request.form["username"]
    password = generate_password_hash(request.form["password"])
    try:
        conn = sqlite3.connect("cloud.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect("/")
    except:
        return "<h3>Username already exists! <a href='/signup'>Try again</a></h3>"

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("cloud.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        session["username"] = username
        return redirect("/home")
    else:
        return "<h3>Invalid username or password <a href='/'>Try again</a></h3>"

@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/")
    username = session["username"]

    conn = sqlite3.connect("cloud.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE username=?", (username,))
    files = cursor.fetchall()
    conn.close()
    return render_template("home.html", username=username, files=files)

@app.route("/upload", methods=["POST"])
def upload():
    if "username" not in session:
        return redirect("/")
    username = session["username"]
    file = request.files["file"]
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        conn = sqlite3.connect("cloud.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (username, filename) VALUES (?, ?)", (username, file.filename))
        conn.commit()
        conn.close()
    return redirect("/home")

@app.route("/download/<filename>")
def download(filename):
    if "username" not in session:
        return redirect("/")
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
