# SIPAM-AI — Monitor Selection Predictor Microservice

Flask-based AI microservice that predicts whether a student will be selected as an academic
monitor. Uses three models: **Random Forest**, **XGBoost**, and **Neural Network (TensorFlow)**.

## Quick Start

```powershell
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Extract dataset from PostgreSQL (make sure sipam_db is running)
python data/extract_dataset.py

# 4. Prepare data (clean, encode, 70/15/15 split, SMOTE if needed)
python data/prepare_dataset.py

# 5. Train all 3 models and save the best one
python models/train.py

# 6. Start the Flask API (port 5001)
python app.py
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/sipam_db` | PostgreSQL connection |
| `AI_PORT` | `5001` | Flask port |
| `FLASK_DEBUG` | `0` | Enable debug mode |

## API Endpoints

### `GET /health`
Returns service status.

### `POST /predict`
Predicts whether a student will be selected as monitor.

**Request body:**
```json
{
  "promedio": 4.1,
  "porcentaje_creditos": 65.0,
  "nota_asignatura": 4.5,
  "nota_entrevista": 4.2,
  "tipo_monitoria": "academica",
  "semestre_asignatura": 4,
  "creditos_asignatura": 3,
  "num_postulantes": 8,
  "num_monitores_requeridos": 2
}
```

**Response:**
```json
{
  "selected_probability": 0.82,
  "prediction": "selected",
  "confidence": "high",
  "model_used": "XGBoost",
  "puntaje_estimado": 4.23,
  "rank_estimado": 1,
  "selection_ratio": 0.25
}
```

### `GET /models/metrics`
Returns accuracy, F1, and AUC-ROC for all 3 models on the test set.

### `GET /models/feature-importance`
Returns feature importances from the best model (tree-based only).

## Running Tests

```powershell
pytest tests/test_predict.py -v
```

## ML Pipeline

```
sipam_db → extract_dataset.py → prepare_dataset.py → train.py → predict.py → app.py
              (real student data)   (70/15/15 split)   (3 models)  (inference)  (Flask API)
```

## Project Structure

```
ai_service/
├── data/
│   ├── extract_dataset.py    # AI-01: Extract from DB + generate synthetic apps
│   ├── prepare_dataset.py    # AI-02: Clean, encode, split, SMOTE
│   └── dataset.csv           # Generated dataset
├── models/
│   ├── train.py              # AI-03/04/05/06: Train, compare, serialize
│   └── saved/
│       ├── preprocessor.joblib
│       ├── random_forest.joblib
│       ├── xgboost.joblib
│       ├── neural_net.h5
│       ├── training_results.json
│       └── best_model.txt
├── predict.py                # AI-07: Inference (separate from training)
├── app.py                    # Flask API
├── requirements.txt
└── tests/
    └── test_predict.py
```
