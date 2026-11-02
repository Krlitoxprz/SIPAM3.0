"""Validación de parámetros de la calculadora de transporte."""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import get_token, auth


@pytest.mark.parametrize("campo,valor", [
    ("num_vehiculos", 0),
    ("num_vehiculos", -5),
    ("num_vehiculos", 21),
    ("categoria_peaje", 0),
    ("categoria_peaje", 6),
])
def test_calcular_ruta_rechaza_valores_fuera_de_rango(client: TestClient, usuario_profesor,
                                                      monkeypatch, campo, valor):
    from app.api.v1.endpoints import transporte

    async def _no_llamar(*args, **kwargs):
        raise AssertionError("no debe consultarse ORS con parámetros inválidos")

    monkeypatch.setattr(transporte, "calcular_ruta", _no_llamar)
    client.cookies.clear()
    token = get_token(client, usuario_profesor.codigo)
    body = {"origen": "Neiva", "destino": "Pitalito", campo: valor}
    r = client.post("/api/v1/transporte/rutas/calcular", json=body, headers=auth(token))
    assert r.status_code == 422


@pytest.mark.parametrize("valor", [0, -1, 21])
def test_costos_practica_rechaza_num_vehiculos_fuera_de_rango(client: TestClient,
                                                              usuario_profesor, valor):
    client.cookies.clear()
    token = get_token(client, usuario_profesor.codigo)
    r = client.get(f"/api/v1/transporte/costos/1?num_vehiculos={valor}", headers=auth(token))
    assert r.status_code == 422
