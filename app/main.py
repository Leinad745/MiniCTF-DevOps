"""Microservicio FastAPI: mini plataforma CTF de una sola vista.

Expone tres desafios clasicos e intencionalmente vulnerables con fines
educativos (entorno controlado de aprendizaje):

1. Inyeccion SQL  -> POST /api/sqli
2. SSTI           -> POST /api/ssti
3. XSS reflejado  -> POST /api/xss

Ademas sirve la vista unica (/) y un endpoint de salud (/health) requerido
por el HEALTHCHECK del contenedor.
"""

import os
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.config import SSTI_FLAG, XSS_FLAG
from app.database import get_connection, init_db

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos al arrancar el servicio."""
    init_db()
    yield


app = FastAPI(
    title="Mini Plataforma CTF",
    description="Tres desafios educativos: SQLi, SSTI y XSS.",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------------------------------- #
# Modelos de entrada
# --------------------------------------------------------------------------- #
class LoginInput(BaseModel):
    username: str = ""
    password: str = ""


class PayloadInput(BaseModel):
    payload: str = ""


# --------------------------------------------------------------------------- #
# Rutas basicas
# --------------------------------------------------------------------------- #
@app.get("/health", tags=["infra"])
def health():
    """Endpoint de salud para el HEALTHCHECK del contenedor y el deploy."""
    return {"status": "ok"}


@app.get("/", tags=["ui"])
def index():
    """Sirve la vista unica de la plataforma."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# --------------------------------------------------------------------------- #
# Desafio 1: Inyeccion SQL
# --------------------------------------------------------------------------- #
@app.post("/api/sqli", tags=["challenges"])
def challenge_sqli(data: LoginInput):
    """Login VULNERABLE a inyeccion SQL (concatenacion de cadenas).

    Objetivo del jugador: evadir la autenticacion (p. ej. ' OR '1'='1' -- )
    para recuperar la fila del admin y con ella la flag.
    """
    # VULNERABILIDAD INTENCIONAL: la entrada del usuario se interpola sin
    # parametrizar. Nunca hacer esto en produccion.
    query = (
        "SELECT username, flag FROM users "
        f"WHERE username = '{data.username}' AND password = '{data.password}'"
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(query)
            row = cur.fetchone()
        except Exception as exc:  # error de sintaxis SQL por payload invalido
            return JSONResponse(
                status_code=400,
                content={"solved": False, "error": f"Error SQL: {exc}", "query": query},
            )
    finally:
        conn.close()

    if row is None:
        return {
            "solved": False,
            "message": "Credenciales invalidas.",
            "query": query,
        }

    flag = row["flag"]
    return {
        "solved": flag is not None,
        "message": f"Sesion iniciada como '{row['username']}'.",
        "flag": flag,
        "query": query,
    }


# --------------------------------------------------------------------------- #
# Desafio 2: SSTI (Server-Side Template Injection)
# --------------------------------------------------------------------------- #
@app.post("/api/ssti", tags=["challenges"])
def challenge_ssti(data: PayloadInput):
    """Renderizado VULNERABLE a SSTI con Jinja2.

    La entrada del usuario se compila como plantilla sin sandbox. Pistas:
    - `{{ 7*7 }}` demuestra que hay evaluacion del lado del servidor.
    - En el contexto existe un objeto `config` con la flag secreta.
    Objetivo: renderizar `{{ config.SECRET_FLAG }}`.
    """
    # Import local para que un fallo de import no tumbe el arranque del servicio.
    from jinja2 import Template

    # VULNERABILIDAD INTENCIONAL: compilar entrada del usuario como plantilla.
    try:
        rendered = Template(data.payload).render(
            config={"SECRET_FLAG": SSTI_FLAG}
        )
    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content={"solved": False, "error": f"Error de plantilla: {exc}"},
        )

    solved = SSTI_FLAG in rendered
    return {
        "solved": solved,
        "rendered": rendered,
        "flag": SSTI_FLAG if solved else None,
    }


# --------------------------------------------------------------------------- #
# Desafio 3: XSS reflejado
# --------------------------------------------------------------------------- #
# Patron sencillo que reconoce payloads de XSS tipicos.
_XSS_PATTERN = re.compile(
    r"<\s*script|on\w+\s*=|<\s*img|<\s*svg|<\s*iframe|javascript:",
    re.IGNORECASE,
)


@app.post("/api/xss", tags=["challenges"])
def challenge_xss(data: PayloadInput):
    """Reflejo VULNERABLE a XSS.

    El servidor devuelve la entrada SIN sanitizar (`reflected`); el frontend
    la inserta en el DOM via innerHTML, de modo que un `<script>`/`onerror`
    se ejecuta. Objetivo: inyectar un payload de script valido.
    """
    solved = bool(_XSS_PATTERN.search(data.payload))
    return {
        "solved": solved,
        # VULNERABILIDAD INTENCIONAL: se refleja la entrada sin escapar.
        "reflected": data.payload,
        "flag": XSS_FLAG if solved else None,
    }
