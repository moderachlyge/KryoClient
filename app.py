import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, session, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv(Path(__file__).resolve().parent / ".env")
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "kryoclient.db"))

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "change-me"),
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def db():
    if DATABASE_URL:
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not DATABASE_URL:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = db()
    if DATABASE_URL:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(32) NOT NULL,
                email VARCHAR(160) NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()


def query_one(sql, params=()):
    conn = db()
    try:
        row = conn.execute(sql, params).fetchone()
        return row
    finally:
        conn.close()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    try:
        query_one("SELECT 1")
        return jsonify(status="ok", database="ok")
    except Exception:
        return jsonify(status="error", database="error"), 503


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if len(name) < 2 or len(name) > 32:
        return jsonify(error="Никнейм должен быть от 2 до 32 символов"), 400
    if "@" not in email or len(email) > 160:
        return jsonify(error="Введите корректный email"), 400
    if len(password) < 6:
        return jsonify(error="Пароль должен содержать минимум 6 символов"), 400

    conn = db()
    try:
        if DATABASE_URL:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (name, email, generate_password_hash(password)),
            )
        else:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
        conn.commit()
        user_id = cur.fetchone()["id"] if DATABASE_URL else cur.lastrowid
    except Exception as exc:
        conn.rollback()
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            conn.close()
            return jsonify(error="Этот email уже зарегистрирован"), 409
        conn.close()
        raise
    conn.close()
    session["user_id"] = user_id
    return jsonify(ok=True)


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if DATABASE_URL:
        user = query_one(
            "SELECT id, name, email, password_hash FROM users WHERE LOWER(email) = %s",
            (email,),
        )
    else:
        user = query_one(
            "SELECT id, name, email, password_hash FROM users WHERE email = ? COLLATE NOCASE",
            (email,),
        )

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Неверный email или пароль"), 401

    session["user_id"] = user["id"]
    return jsonify(ok=True)


@app.get("/api/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(user=None)

    user = query_one(
        "SELECT id, name, email, created_at FROM users WHERE id = %s" if DATABASE_URL else "SELECT id, name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    if not user:
        session.clear()
        return jsonify(user=None)

    return jsonify(user=dict(user))


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
