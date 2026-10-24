#!/bin/bash
# ── AI Service entrypoint ─────────────────────────────────────────────────────
# Trains the model pipeline on first run, then starts Flask.
# Safe to run on Linux even if edited on Windows (CRLF stripped below).
set -e

# Strip Windows CRLF if present (edited on Windows)
sed -i 's/\r//' "$0" 2>/dev/null || true

MODELS_DIR="/app/models/saved"
BEST_MODEL="$MODELS_DIR/best_model.txt"

if [ ! -f "$BEST_MODEL" ]; then
    echo "[entrypoint] No trained model found. Waiting for DB to have seed data..."
    # Wait up to 3 minutes for the users table to have data
    RETRIES=18
    until python -c "
import psycopg2, os, sys
try:
    conn = psycopg2.connect(os.environ.get('DB_URL',''))
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM users')
    count = cur.fetchone()[0]
    conn.close()
    sys.exit(0 if count >= 10 else 1)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
        RETRIES=$((RETRIES - 1))
        if [ $RETRIES -eq 0 ]; then
            echo "[entrypoint] DB not ready or no seed data. Starting Flask without training."
            break
        fi
        echo "[entrypoint] Waiting for seed data... ($RETRIES retries left)"
        sleep 10
    done

    if [ -f "$BEST_MODEL" ]; then
        echo "[entrypoint] Model already trained by another process, skipping."
    else
        echo "[entrypoint] Running full training pipeline..."
        python data/extract_dataset.py && \
        python data/prepare_dataset.py && \
        python models/train.py && \
        echo "[entrypoint] Training complete." || \
        echo "[entrypoint] Training failed — Flask will start anyway (AI features limited)."
    fi
else
    echo "[entrypoint] Trained model found: $(cat $BEST_MODEL). Skipping training."
fi

echo "[entrypoint] Starting Flask AI service on port 5001 (gunicorn)..."
exec gunicorn app:app \
    --bind 0.0.0.0:5001 \
    --workers 2 \
    --timeout 120 \
    --preload \
    --access-logfile - \
    --error-logfile -
