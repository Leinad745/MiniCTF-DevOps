"""Capa de persistencia con SQLite.

Usamos sqlite3 directamente (sin ORM) para que el desafio de Inyeccion SQL
sea autentico: la consulta se construye por concatenacion de cadenas, tal
como ocurre en el codigo vulnerable del mundo real.
"""

import os
import sqlite3

from app.config import ADMIN_PASSWORD, ADMIN_USER, SQLI_FLAG

# Ruta del archivo de base de datos. Se puede sobrescribir con la variable de
# entorno CTF_DB_PATH (util para las pruebas, que usan una BD aislada).
DB_PATH = os.environ.get(
    "CTF_DB_PATH",
    os.path.join(os.path.dirname(__file__), "ctf.db"),
)


def get_connection() -> sqlite3.Connection:
    """Devuelve una conexion a SQLite con filas accesibles por nombre."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crea la tabla de usuarios y la siembra con datos iniciales.

    Reinicia el contenido en cada llamada para que el estado del desafio sea
    deterministico (importante tanto al arrancar el servicio como en tests).
    """
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
