"""
AI-03/04/05/06 — Train 3 models + Stacking Ensemble.
Improvements v2:
  - Optuna hyperparameter tuning (replaces GridSearchCV)
  - Stacking Ensemble (RF + XGBoost as base, LogisticRegression as meta)
  - Stratified K-Fold cross-validation (5 folds)
  - CalibratedClassifierCV for well-calibrated probabilities
  - SHAP background data saved for explainability
"""
import json
import sys
import warnings
import numpy as np
import joblib
from pathlib import Path
from sklearn.base import BaseEstimator, ClassifierMixin

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent.parent))

MODELS_DIR = Path(__file__).parent / "saved"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
N_OPTUNA_TRIALS = 40
N_FOLDS = 5


# ── Load pre-processed splits ──────────────────────────────────────────────
def load_splits():
    X_train = np.load(MODELS_DIR / "X_train.npy")
    X_val   = np.load(MODELS_DIR / "X_val.npy")
    X_test  = np.load(MODELS_DIR / "X_test.npy")
    y_train = np.load(MODELS_DIR / "y_train.npy")
    y_val   = np.load(MODELS_DIR / "y_val.npy")
    y_test  = np.load(MODELS_DIR / "y_test.npy")
    return X_train, X_val, X_test, y_train, y_val, y_test


# ── Metrics helper ─────────────────────────────────────────────────────────
def compute_metrics(model, X, y) -> dict:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score,
        f1_score, roc_auc_score, confusion_matrix,
    )
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    cm = confusion_matrix(y, y_pred).tolist()
    return {
        "accuracy":         round(float(accuracy_score(y, y_pred)), 4),
        "precision":        round(float(precision_score(y, y_pred, zero_division=0)), 4),
        "recall":           round(float(recall_score(y, y_pred, zero_division=0)), 4),
        "f1":               round(float(f1_score(y, y_pred, zero_division=0)), 4),
        "roc_auc":          round(float(roc_auc_score(y, y_prob)), 4),
        "confusion_matrix": cm,
    }


def kfold_metrics(model_factory, X, y) -> dict:
    """Run stratified K-Fold and return mean ± std of key metrics."""
    from sklearn.model_selection import StratifiedKFold, cross_validate
    cv = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scoring = ["accuracy", "f1", "roc_auc", "precision", "recall"]
    results = cross_validate(model_factory(), X, y, cv=cv, scoring=scoring, n_jobs=-1)
    summary = {}
    for metric in scoring:
        vals = results[f"test_{metric}"]
        summary[metric] = {
            "mean": round(float(vals.mean()), 4),
            "std":  round(float(vals.std()), 4),
        }
    print(f"  K-Fold (n={N_FOLDS}) — "
          + " | ".join(f"{m}: {v['mean']:.3f}±{v['std']:.3f}" for m, v in summary.items()))
    return summary


# ── Model 1: Random Forest with Optuna ────────────────────────────────────
def train_random_forest(X_train, y_train, X_val, y_val):
    import optuna
    from sklearn.ensemble import RandomForestClassifier

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    print("\n[train] Tuning Random Forest with Optuna ...")

    def objective(trial):
        from sklearn.model_selection import cross_val_score
        params = {
            "n_estimators":    trial.suggest_int("n_estimators", 100, 500),
            "max_depth":       trial.suggest_int("max_depth", 4, 20),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
            "min_samples_leaf":  trial.suggest_int("min_samples_leaf", 1, 5),
            "max_features":    trial.suggest_categorical("max_features", ["sqrt", "log2"]),
        }
        m = RandomForestClassifier(**params, random_state=RANDOM_STATE, class_weight="balanced", n_jobs=-1)
        return cross_val_score(m, X_train, y_train, cv=3, scoring="f1").mean()

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=N_OPTUNA_TRIALS, show_progress_bar=False)
    print(f"[train] RF best params: {study.best_params}  (F1={study.best_value:.4f})")

    best = RandomForestClassifier(**study.best_params, random_state=RANDOM_STATE,
                                  class_weight="balanced", n_jobs=-1)
    best.fit(X_train, y_train)
    metrics = compute_metrics(best, X_val, y_val)
    print(f"[train] RF val metrics: {metrics}")

    kfold_metrics(
        lambda: RandomForestClassifier(**study.best_params, random_state=RANDOM_STATE,
                                       class_weight="balanced", n_jobs=-1),
        np.vstack([X_train, X_val]), np.concatenate([y_train, y_val])
    )

    joblib.dump(best, MODELS_DIR / "random_forest.joblib")
    return best, metrics


# ── Model 2: XGBoost with Optuna ──────────────────────────────────────────
def train_xgboost(X_train, y_train, X_val, y_val):
    import optuna
    from xgboost import XGBClassifier

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    print("\n[train] Tuning XGBoost with Optuna ...")
    scale_pos = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))

    def objective(trial):
        from sklearn.model_selection import cross_val_score
        params = {
            "n_estimators":   trial.suggest_int("n_estimators", 100, 400),
            "max_depth":      trial.suggest_int("max_depth", 3, 10),
            "learning_rate":  trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample":      trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha":      trial.suggest_float("reg_alpha", 0.0, 1.0),
            "reg_lambda":     trial.suggest_float("reg_lambda", 0.5, 3.0),
        }
        m = XGBClassifier(**params, scale_pos_weight=scale_pos, random_state=RANDOM_STATE,
                          eval_metric="logloss", n_jobs=-1)
        return cross_val_score(m, X_train, y_train, cv=3, scoring="f1").mean()

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=N_OPTUNA_TRIALS, show_progress_bar=False)
    print(f"[train] XGB best params: {study.best_params}  (F1={study.best_value:.4f})")

    best = XGBClassifier(**study.best_params, scale_pos_weight=scale_pos,
                         random_state=RANDOM_STATE, eval_metric="logloss", n_jobs=-1)
    best.fit(X_train, y_train)
    metrics = compute_metrics(best, X_val, y_val)
    print(f"[train] XGB val metrics: {metrics}")

    kfold_metrics(
        lambda: XGBClassifier(**study.best_params, scale_pos_weight=scale_pos,
                              random_state=RANDOM_STATE, eval_metric="logloss", n_jobs=-1),
        np.vstack([X_train, X_val]), np.concatenate([y_train, y_val])
    )

    joblib.dump(best, MODELS_DIR / "xgboost.joblib")
    return best, metrics


# ── sklearn wrapper for Keras (module-level so pickle can serialize it) ───────

class NNSklearnWrapper(BaseEstimator, ClassifierMixin):
    """sklearn-compatible wrapper around a trained Keras model."""
    def __init__(self, keras_model):
        self._m = keras_model
        self.classes_ = np.array([0, 1])

    def fit(self, X, y):
        return self

    def predict(self, X):
        return (self._m.predict(X, verbose=0) > 0.5).astype(int).flatten()

    def predict_proba(self, X):
        p = self._m.predict(X, verbose=0).flatten()
        return np.column_stack([1 - p, p])


# ── Model 3: Neural Network (TensorFlow) ──────────────────────────────────
def train_neural_network(X_train, y_train, X_val, y_val):
    import tensorflow as tf
    from tensorflow.keras import layers, callbacks

    print("\n[train] Training Neural Network (TensorFlow) ...")
    tf.random.set_seed(RANDOM_STATE)
    n_features = X_train.shape[1]

    model = tf.keras.Sequential([
        layers.Input(shape=(n_features,)),
        layers.Dense(128, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(64, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(32, activation="relu"),
        layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )

    cw = {0: 1.0, 1: float((y_train == 0).sum() / max((y_train == 1).sum(), 1))}
    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=120, batch_size=32, class_weight=cw,
        callbacks=[
            callbacks.EarlyStopping(monitor="val_loss", patience=12, restore_best_weights=True),
            callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=6, min_lr=1e-6),
        ],
        verbose=0,
    )
    model.save(MODELS_DIR / "neural_net.h5")

    wrapper = NNSklearnWrapper(model)
    metrics = compute_metrics(wrapper, X_val, y_val)
    print(f"[train] NN val metrics: {metrics}")
    joblib.dump(wrapper, MODELS_DIR / "neural_net_wrapper.joblib")
    return wrapper, metrics


# ── Model 4: Stacking Ensemble ────────────────────────────────────────────
def train_stacking(rf, xgb, X_train, y_train, X_val, y_val):
    from sklearn.ensemble import StackingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.calibration import CalibratedClassifierCV

    print("\n[train] Training Stacking Ensemble (RF + XGB → LR meta) ...")
    stack = StackingClassifier(
        estimators=[
            ("rf",  rf),
            ("xgb", xgb),
        ],
        final_estimator=LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        cv=5, passthrough=False, n_jobs=-1,
    )
    stack.fit(X_train, y_train)

    # Calibrate probabilities so outputs are reliable
    calibrated = CalibratedClassifierCV(stack, cv="prefit", method="isotonic")
    calibrated.fit(X_val, y_val)

    metrics = compute_metrics(calibrated, X_val, y_val)
    print(f"[train] Stacking (calibrated) val metrics: {metrics}")

    joblib.dump(calibrated, MODELS_DIR / "stacking_calibrated.joblib")

    # Save SHAP background data (100 samples from train set for KernelExplainer)
    idx = np.random.choice(len(X_train), min(100, len(X_train)), replace=False)
    np.save(MODELS_DIR / "shap_background.npy", X_train[idx])

    return calibrated, metrics


# ── Compare and select best ────────────────────────────────────────────────
def select_best(metrics_dict: dict) -> str:
    return max(metrics_dict, key=lambda k: metrics_dict[k]["f1"])


def main():
    print("[train] Loading processed data splits ...")
    X_train, X_val, X_test, y_train, y_val, y_test = load_splits()
    X_trainval = np.vstack([X_train, X_val])
    y_trainval  = np.concatenate([y_train, y_val])

    rf_model,  rf_metrics  = train_random_forest(X_train, y_train, X_val, y_val)
    xgb_model, xgb_metrics = train_xgboost(X_train, y_train, X_val, y_val)
    nn_wrapper, nn_metrics = train_neural_network(X_train, y_train, X_val, y_val)
    stack_model, stack_metrics = train_stacking(rf_model, xgb_model,
                                                X_trainval, y_trainval, X_test, y_test)

    # ── Test set evaluation ────────────────────────────────────────────────
    print("\n[train] ── Test set evaluation ──────────────────────────────────")
    test_metrics = {
        "RandomForest":  compute_metrics(rf_model,    X_test, y_test),
        "XGBoost":       compute_metrics(xgb_model,   X_test, y_test),
        "NeuralNetwork": compute_metrics(nn_wrapper,  X_test, y_test),
        "Stacking":      compute_metrics(stack_model, X_test, y_test),
    }
    for name, m in test_metrics.items():
        print(f"  {name:20s}  acc={m['accuracy']}  f1={m['f1']}  auc={m['roc_auc']}")

    best_name = select_best(test_metrics)
    print(f"\n[train] Best model: {best_name} (by F1 on test set)")

    results = {
        "val_metrics":  {"RandomForest": rf_metrics, "XGBoost": xgb_metrics,
                         "NeuralNetwork": nn_metrics, "Stacking": stack_metrics},
        "test_metrics": test_metrics,
        "best_model":   best_name,
        "kfold_folds":  N_FOLDS,
        "optuna_trials": N_OPTUNA_TRIALS,
    }
    with open(MODELS_DIR / "training_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(MODELS_DIR / "best_model.txt", "w") as f:
        f.write(best_name)

    print(f"[train] Results saved to {MODELS_DIR / 'training_results.json'}")
    return results


if __name__ == "__main__":
    main()
