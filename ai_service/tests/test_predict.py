"""
TEST-01 — Unit tests for the Flask AI microservice.
Run with: pytest ai_service/tests/test_predict.py -v
"""
import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as flask_app

VALID_PAYLOAD = {
    "promedio": 4.1,
    "porcentaje_creditos": 65.0,
    "nota_asignatura": 4.5,
    "nota_entrevista": 4.2,
    "tipo_monitoria": "academica",
    "semestre_asignatura": 4,
    "creditos_asignatura": 3,
    "num_postulantes": 8,
    "num_monitores_requeridos": 2,
}


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ── UT-01 ────────────────────────────────────────────────────────────────────
def test_predict_valid_input(client):
    """UT-01: Valid payload returns 200 with probability in [0, 1]."""
    res = client.post("/predict", json=VALID_PAYLOAD)
    assert res.status_code == 200
    data = res.get_json()
    assert "selected_probability" in data
    assert 0.0 <= data["selected_probability"] <= 1.0
    assert data["prediction"] in ("selected", "not_selected")
    assert data["confidence"] in ("high", "medium")


# ── UT-02 ────────────────────────────────────────────────────────────────────
def test_predict_missing_required_field(client):
    """UT-02: Missing required field returns 422."""
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "promedio"}
    res = client.post("/predict", json=payload)
    assert res.status_code == 422
    data = res.get_json()
    assert "detail" in data
    assert "promedio" in str(data["detail"])


# ── UT-03 ────────────────────────────────────────────────────────────────────
def test_predict_invalid_promedio(client):
    """UT-03: promedio > 5.0 returns 422."""
    payload = {**VALID_PAYLOAD, "promedio": 6.0}
    res = client.post("/predict", json=payload)
    assert res.status_code == 422


# ── UT-04 ────────────────────────────────────────────────────────────────────
def test_models_metrics_returns_all_models(client):
    """UT-04: /models/metrics returns data for all 4 models (RF, XGB, NN, Stacking)."""
    res = client.get("/models/metrics")
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        data = res.get_json()
        assert "test_metrics" in data
        assert "best_model" in data
        for name in ("RandomForest", "XGBoost", "NeuralNetwork", "Stacking"):
            assert name in data["test_metrics"], f"Model '{name}' missing from test_metrics"
            for metric in ("accuracy", "f1", "roc_auc"):
                assert metric in data["test_metrics"][name]


# ── UT-06 ────────────────────────────────────────────────────────────────────
def test_predict_high_performing_student(client):
    """UT-06: Student with max features should have high probability."""
    payload = {
        **VALID_PAYLOAD,
        "promedio": 4.9,
        "porcentaje_creditos": 95.0,
        "nota_asignatura": 5.0,
        "nota_entrevista": 5.0,
        "num_postulantes": 10,
        "num_monitores_requeridos": 3,
    }
    res = client.post("/predict", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["selected_probability"] >= 0.6


# ── UT-07 ────────────────────────────────────────────────────────────────────
def test_predict_low_performing_student(client):
    """UT-07: Student at minimum eligibility threshold should have lower probability."""
    payload = {
        **VALID_PAYLOAD,
        "promedio": 3.5,
        "porcentaje_creditos": 30.0,
        "nota_asignatura": 3.0,
        "nota_entrevista": 2.5,
        "num_postulantes": 15,
        "num_monitores_requeridos": 1,
    }
    res = client.post("/predict", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["selected_probability"] <= 0.6


# ── Health check ────────────────────────────────────────────────────────────
def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


# ── 404 ─────────────────────────────────────────────────────────────────────
def test_unknown_route(client):
    res = client.get("/nonexistent")
    assert res.status_code == 404
