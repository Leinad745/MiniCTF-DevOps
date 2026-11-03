# Capa de persistencia con SQLite.

import os
import sqlite3

from app.config import ADMIN_PASSWORD, ADMIN_USER, SQLI_FLAG

DB_PATH = os.environ.get(
    "CTF_DB_PATH",
    os.path.join(os.path.dirname(__file__), "ctf.db"),
)


def get_connection() -> sqlite3.Connection:
    # Devuelve una conexion a SQLite con filas accesibles por nombre.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    #Crea la tabla de usuarios y la siembra con datos iniciales.
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                flag     TEXT
            )
            """
        )
        cur.execute("DELETE FROM users")
        # El admin posee la flag; un login legitimo requiere la clave secreta.
        cur.execute(
            "INSERT INTO users (username, password, flag) VALUES (?, ?, ?)",
            (ADMIN_USER, ADMIN_PASSWORD, SQLI_FLAG),
        )
        # Usuario normal sin flag (permite probar un login valido benigno).
        cur.execute(
            "INSERT INTO users (username, password, flag) VALUES (?, ?, ?)",
            ("guest", "guest", None),
        )
        conn.commit()
    finally:
        conn.close()
