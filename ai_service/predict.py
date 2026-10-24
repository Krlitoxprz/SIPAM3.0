"""
AI-07 — Inference script (separate from training).
Loads the serialized best model and preprocessor, makes predictions.
"""
import json
import numpy as np
import joblib
from pathlib import Path
from typing import Any

MODELS_DIR = Path(__file__).parent / "models" / "saved"

_preprocessor = None
_model = None
_model_name = None
_feature_meta = None


def _load_artifacts():
    global _preprocessor, _model, _model_name, _feature_meta

    if _preprocessor is None:
        _preprocessor = joblib.load(MODELS_DIR / "preprocessor.joblib")

    if _feature_meta is None:
        with open(MODELS_DIR / "feature_meta.json", encoding="utf-8") as f:
            _feature_meta = json.load(f)

    if _model is None:
        best_file = MODELS_DIR / "best_model.txt"
        if not best_file.exists():
            raise FileNotFoundError("best_model.txt not found. Run train.py first.")
        _model_name = best_file.read_text().strip()

        filename_map = {
            "RandomForest": "random_forest.joblib",
            "XGBoost":      "xgboost.joblib",
            "Stacking":     "stacking_calibrated.joblib",
        }
        if _model_name == "NeuralNetwork":
            import tensorflow as tf
            _model = tf.keras.models.load_model(MODELS_DIR / "neural_net.h5")
        else:
            fname = filename_map.get(_model_name, "stacking_calibrated.joblib")
            _model = joblib.load(MODELS_DIR / fname)

    return _preprocessor, _model, _model_name, _feature_meta


def predict(features: dict) -> dict:
    """
    Parameters
    ----------
    features : dict with keys:
        promedio, porcentaje_creditos, nota_asignatura, nota_entrevista,
        tipo_monitoria, semestre_asignatura, creditos_asignatura,
        num_postulantes, num_monitores_requeridos

    Returns
    -------
    dict with selected_probability, prediction, confidence, model_used,
    puntaje_estimado, rank_estimado
    """
    preprocessor, model, model_name, meta = _load_artifacts()

    import pandas as pd
    numeric_features = meta["numeric_features"]
    categorical_features = meta["categorical_features"]

    row = {col: features[col] for col in numeric_features + categorical_features
            if col in features}
    # Compute engineered features if not provided
    if "ratio_competencia" not in row:
        row["ratio_competencia"] = round(
            float(features.get("num_monitores_requeridos", 1))
            / max(float(features.get("num_postulantes", 6)), 1), 4
        )
    if "puntaje_formula" not in row:
        row["puntaje_formula"] = round(
            float(features.get("nota_asignatura", 0)) * 0.30
            + float(features.get("promedio", 0)) * 0.30
            + float(features.get("nota_entrevista", 3.5)) * 0.40, 4
        )
    for col in numeric_features + categorical_features:
        if col not in row:
            row[col] = 0
    X_raw = pd.DataFrame([row])
    X_proc = preprocessor.transform(X_raw)

    if model_name == "NeuralNetwork":
        prob = float(model.predict(X_proc, verbose=0).flatten()[0])
    else:
        prob = float(model.predict_proba(X_proc)[0, 1])

    prediction = "selected" if prob >= 0.5 else "not_selected"
    confidence = "high" if prob >= 0.75 or prob <= 0.25 else "medium"

    puntaje_estimado = round(
        float(features["nota_asignatura"]) * 0.30
        + float(features["promedio"]) * 0.30
        + float(features.get("nota_entrevista", 0)) * 0.40,
        4,
    )

    n_post = int(features.get("num_postulantes", 5))
    n_mon = int(features.get("num_monitores_requeridos", 1))
    ratio = n_mon / max(n_post, 1)
    rank_estimado = max(1, round(n_post * (1 - prob) + 0.5))

    return {
        "selected_probability": round(prob, 4),
        "prediction": prediction,
        "confidence": confidence,
        "model_used": model_name,
        "puntaje_estimado": puntaje_estimado,
        "rank_estimado": rank_estimado,
        "selection_ratio": round(ratio, 3),
    }


def get_model_metrics() -> dict:
    results_path = MODELS_DIR / "training_results.json"
    if not results_path.exists():
        raise FileNotFoundError("training_results.json not found. Run train.py first.")
    with open(results_path, encoding="utf-8") as f:
        return json.load(f)


def get_feature_importance() -> dict | None:
    _, model, model_name, meta = _load_artifacts()
    # For stacking, try to get RF sub-estimator importances
    actual_model = model
    if model_name == "Stacking" and hasattr(model, "estimator"):
        actual_model = model.estimator
    if hasattr(actual_model, "estimators_"):  # StackingClassifier
        for name, est in actual_model.estimators_:
            if hasattr(est, "feature_importances_"):
                names = meta["feature_names"]
                importances = est.feature_importances_.tolist()
                paired = sorted(zip(names, importances), key=lambda x: x[1], reverse=True)
                return {n: round(imp, 6) for n, imp in paired}
    if hasattr(actual_model, "feature_importances_"):
        names = meta["feature_names"]
        importances = actual_model.feature_importances_.tolist()
        paired = sorted(zip(names, importances), key=lambda x: x[1], reverse=True)
        return {n: round(imp, 6) for n, imp in paired}
    return None


def explain(features: dict) -> dict:
    """
    Returns SHAP values for the given prediction using KernelExplainer.
    Works with any model (tree or neural network).
    """
    import shap
    preprocessor, model, model_name, meta = _load_artifacts()

    import pandas as pd
    numeric_features = meta["numeric_features"]
    categorical_features = meta["categorical_features"]
    row = {col: features[col] for col in numeric_features + categorical_features
            if col in features}
    if "ratio_competencia" not in row:
        row["ratio_competencia"] = round(
            float(features.get("num_monitores_requeridos", 1))
            / max(float(features.get("num_postulantes", 6)), 1), 4
        )
    if "puntaje_formula" not in row:
        row["puntaje_formula"] = round(
            float(features.get("nota_asignatura", 0)) * 0.30
            + float(features.get("promedio", 0)) * 0.30
            + float(features.get("nota_entrevista", 3.5)) * 0.40, 4
        )
    for col in numeric_features + categorical_features:
        if col not in row:
            row[col] = 0
    X_raw = pd.DataFrame([row])
    X_proc = preprocessor.transform(X_raw)

    background_path = MODELS_DIR / "shap_background.npy"
    if not background_path.exists():
        return {"error": "SHAP background data not found. Re-run train.py."}

    background = np.load(background_path)
    feature_names = meta["feature_names"]

    def predict_fn(X):
        if model_name == "NeuralNetwork":
            return model.predict(X, verbose=0).flatten()
        return model.predict_proba(X)[:, 1]

    explainer = shap.KernelExplainer(predict_fn, shap.kmeans(background, 20))
    shap_values = explainer.shap_values(X_proc, nsamples=100)

    values = shap_values[0].tolist() if hasattr(shap_values[0], "tolist") else list(shap_values[0])
    explanation = sorted(
        [{"feature": n, "shap_value": round(v, 5)} for n, v in zip(feature_names, values)],
        key=lambda x: abs(x["shap_value"]), reverse=True
    )
    return {
        "base_value": round(float(explainer.expected_value), 4),
        "top_features": explanation[:8],
        "model_used": model_name,
    }


if __name__ == "__main__":
    sample = {
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
    result = predict(sample)
    print("Prediction result:", json.dumps(result, indent=2))
