"""Pruebas unitarias de la mini plataforma CTF.

Cubren los casos criticos: infraestructura (salud / vista) y la logica de
cada uno de los tres desafios, tanto el camino benigno (no resuelto) como la
explotacion exitosa (flag capturada).
"""

from app.config import SQLI_FLAG, SSTI_FLAG, XSS_FLAG


# --------------------------------------------------------------------------- #
# Infraestructura
# --------------------------------------------------------------------------- #
def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_index_sirve_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Mini Plataforma CTF" in resp.text


# --------------------------------------------------------------------------- #
# Desafio 1: Inyeccion SQL
# --------------------------------------------------------------------------- #
def test_sqli_login_normal_sin_flag(client):
    """Un login valido benigno (guest) no entrega flag."""
    resp = client.post("/api/sqli", json={"username": "guest", "password": "guest"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["solved"] is False
    assert body["flag"] is None


def test_sqli_credenciales_invalidas(client):
    resp = client.post("/api/sqli", json={"username": "admin", "password": "mala"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["solved"] is False


def test_sqli_inyeccion_entrega_flag(client):
    """El bypass clasico ' OR '1'='1' -- recupera la flag del admin."""
    resp = client.post(
        "/api/sqli",
        json={"username": "admin' OR '1'='1' -- ", "password": "x"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["solved"] is True
    assert body["flag"] == SQLI_FLAG


# --------------------------------------------------------------------------- #
# Desafio 2: SSTI
# --------------------------------------------------------------------------- #
def test_ssti_evaluacion_aritmetica(client):
    """`{{ 7*7 }}` demuestra evaluacion del lado del servidor, sin flag."""
    resp = client.post("/api/ssti", json={"payload": "{{ 7*7 }}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["rendered"] == "49"
    assert body["solved"] is False


def test_ssti_extrae_flag(client):
    resp = client.post("/api/ssti", json={"payload": "{{ config.SECRET_FLAG }}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["solved"] is True
    assert body["flag"] == SSTI_FLAG


def test_ssti_payload_invalido_devuelve_error(client):
    resp = client.post("/api/ssti", json={"payload": "{{ "})
    assert resp.status_code == 400
    assert resp.json()["solved"] is False


# --------------------------------------------------------------------------- #
# Desafio 3: XSS
# --------------------------------------------------------------------------- #
def test_xss_texto_plano_no_resuelve(client):
    resp = client.post("/api/xss", json={"payload": "hola mundo"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["solved"] is False
    assert body["flag"] is None
    # Se refleja la entrada tal cual (comportamiento vulnerable intencional).
    assert body["reflected"] == "hola mundo"


def test_xss_script_entrega_flag(client):
    resp = client.post(
        "/api/xss", json={"payload": "<script>alert(1)</script>"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["solved"] is True
    assert body["flag"] == XSS_FLAG


def test_xss_img_onerror_entrega_flag(client):
    resp = client.post(
        "/api/xss", json={"payload": "<img src=x onerror=alert(1)>"}
    )
    assert resp.status_code == 200
    assert resp.json()["solved"] is True
