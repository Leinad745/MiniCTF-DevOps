"""Configuracion compartida de las pruebas.

Fuerza el uso de una base de datos SQLite temporal y aislada para no tocar
la BD real del servicio, e inicializa el esquema antes de cada prueba.
"""

import os
import tempfile

import pytest

# La ruta de BD debe fijarse ANTES de importar modulos que lean DB_PATH.
_TMP_DB = os.path.join(tempfile.gettempdir(), "ctf_test.db")
os.environ["CTF_DB_PATH"] = _TMP_DB

from fastapi.testclient import TestClient  # noqa: E402

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_db():
    """Reinicia la base de datos antes de cada prueba (estado deterministico)."""
    init_db()
    yield


@pytest.fixture
def client():
    """Cliente HTTP de pruebas sobre la app FastAPI."""
    with TestClient(app) as c:
        yield c


def pytest_sessionfinish(session, exitstatus):
    """Limpia el archivo de BD temporal al terminar la sesion de pruebas."""
    if os.path.exists(_TMP_DB):
        os.remove(_TMP_DB)
