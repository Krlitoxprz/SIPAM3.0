"""
test_nlp_batch.py — POST /api/v1/nlp/batch_analyze ante fallos del servicio de IA
"""
import httpx
from fastapi.testclient import TestClient
from tests.conftest import get_token, auth

URL = "/api/v1/nlp/batch_analyze"
TEXTOS = ["Texto de prueba para el análisis por lotes del servicio NLP."]


def _mock_post(monkeypatch, handler):
    async def fake_post(self, url, *args, **kwargs):
        return handler(httpx.Request("POST", url))
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)


def test_batch_servicio_caido_retorna_503(client: TestClient, usuario_profesor, monkeypatch):
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)
    _mock_post(monkeypatch, handler)
    token = get_token(client, usuario_profesor.codigo)
    r = client.post(URL, json=TEXTOS, headers=auth(token))
    assert r.status_code == 503


def test_batch_error_upstream_no_se_devuelve_como_resultado(client: TestClient, usuario_profesor, monkeypatch):
    _mock_post(monkeypatch, lambda request: httpx.Response(500, json={"error": "boom"}, request=request))
    token = get_token(client, usuario_profesor.codigo)
    r = client.post(URL, json=TEXTOS, headers=auth(token))
    assert r.status_code == 500
    assert "NLP service error" in r.json()["detail"]


def test_batch_exito_devuelve_resultados(client: TestClient, usuario_profesor, monkeypatch):
    payload = {"results": [{"quality_score": 2}]}
    _mock_post(monkeypatch, lambda request: httpx.Response(200, json=payload, request=request))
    token = get_token(client, usuario_profesor.codigo)
    r = client.post(URL, json=TEXTOS, headers=auth(token))
    assert r.status_code == 200
    assert r.json() == payload
