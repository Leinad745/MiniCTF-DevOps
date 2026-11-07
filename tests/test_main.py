from app.config import SQLI_FLAG, SSTI_FLAG, XSS_FLAG

# Servicio

def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

# SQLI

def test_sqli_login_normal_sin_flag(client):
    resp = client.post("/api/sqli", json={"username": "guest", "password": "guest"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["solved"] is False
    assert body["flag"] is None

def test_sqli_inyeccion_entrega_flag(client):
    resp = client.post(
        "/api/sqli",
        json={"username": "admin' OR '1'='1' -- ", "password": "x"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["solved"] is True
    assert body["flag"] == SQLI_FLAG

#SSTI

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

# XSS

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