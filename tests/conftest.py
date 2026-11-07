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
    init_db()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def pytest_sessionfinish(session, exitstatus):
    if os.path.exists(_TMP_DB):
        os.remove(_TMP_DB)
