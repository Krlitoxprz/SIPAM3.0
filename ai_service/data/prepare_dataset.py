"""
AI-02 — Data preparation: cleaning, encoding, class balancing, and 70/15/15 split.
Saves split CSV files and the fitted preprocessing pipeline.
"""
import os
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE

RANDOM_STATE = 42
DATA_DIR = Path(__file__).parent
MODELS_DIR = Path(__file__).parent.parent / "models" / "saved"

NUMERIC_FEATURES = [
    "promedio",
    "porcentaje_creditos",
    "nota_asignatura",
    "nota_entrevista",
    "semestre_asignatura",
    "creditos_asignatura",
    "num_postulantes",
    "num_monitores_requeridos",
    "ratio_competencia",     # engineered: monitores / postulantes
    "puntaje_formula",       # engineered: RF-MON-05 formula value
]
CATEGORICAL_FEATURES = ["tipo_monitoria"]
TARGET = "seleccionado"


def load_raw(path: Path = DATA_DIR / "dataset.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"[prepare] Loaded {len(df)} rows from {path}")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET])
    df["promedio"] = df["promedio"].clip(0.0, 5.0)
    df["nota_asignatura"] = df["nota_asignatura"].clip(0.0, 5.0)
    df["nota_entrevista"] = df["nota_entrevista"].clip(0.0, 5.0)
    df["porcentaje_creditos"] = df["porcentaje_creditos"].clip(0.0, 100.0)
    df[TARGET] = df[TARGET].astype(int)
    print(f"[prepare] After cleaning: {len(df)} rows")
    return df


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline([("scaler", StandardScaler())])
    categorical_pipeline = Pipeline([
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def split_and_balance(df: pd.DataFrame):
    """
    Splits into 70/15/15. SMOTE is applied ONLY on the training partition.
    """
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]

    # First split: 70% train, 30% temp
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
    )
    # Second split: 15% val, 15% test (50/50 of the 30%)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp
    )

    print(f"[prepare] Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # Fit preprocessor on training data only
    preprocessor = build_preprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)

    # Class imbalance check — apply SMOTE only on training
    class_counts = y_train.value_counts()
    imbalance_ratio = class_counts.min() / class_counts.max()
    print(f"[prepare] Training class distribution:\n{class_counts}")
    print(f"[prepare] Imbalance ratio: {imbalance_ratio:.2f}")

    if imbalance_ratio < 0.60:
        print("[prepare] Applying SMOTE to training set ...")
        smote = SMOTE(random_state=RANDOM_STATE)
        X_train_proc, y_train = smote.fit_resample(X_train_proc, y_train)
        print(f"[prepare] After SMOTE: {pd.Series(y_train).value_counts().to_dict()}")
    else:
        print("[prepare] No SMOTE needed — classes are balanced.")

    return (
        X_train_proc, X_val_proc, X_test_proc,
        y_train.values, y_val.values, y_test.values,
        preprocessor,
    )


def save_splits(X_train, X_val, X_test, y_train, y_val, y_test, preprocessor):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    np.save(MODELS_DIR / "X_train.npy", X_train)
    np.save(MODELS_DIR / "X_val.npy", X_val)
    np.save(MODELS_DIR / "X_test.npy", X_test)
    np.save(MODELS_DIR / "y_train.npy", y_train)
    np.save(MODELS_DIR / "y_val.npy", y_val)
    np.save(MODELS_DIR / "y_test.npy", y_test)

    joblib.dump(preprocessor, MODELS_DIR / "preprocessor.joblib")

    # Save feature metadata for Flask inference
    cat_encoder = preprocessor.named_transformers_["cat"]["encoder"]
    feature_names = NUMERIC_FEATURES + list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
    meta = {
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "feature_names": feature_names,
        "target": TARGET,
    }
    with open(MODELS_DIR / "feature_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[prepare] All splits and preprocessor saved to {MODELS_DIR}")


def main():
    df = load_raw()
    df = clean(df)
    X_train, X_val, X_test, y_train, y_val, y_test, preprocessor = split_and_balance(df)
    save_splits(X_train, X_val, X_test, y_train, y_val, y_test, preprocessor)
    return X_train, X_val, X_test, y_train, y_val, y_test, preprocessor


if __name__ == "__main__":
    main()
