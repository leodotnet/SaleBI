#!/usr/bin/env bash
set -Eeuo pipefail

# Start the Streamlit app with a local virtualenv and .env
# Usage: PORT=8501 ADDRESS=0.0.0.0 ./start.sh

# Move to repo root (this script's directory)
cd "$(dirname "${BASH_SOURCE[0]}")"

PYTHON_BIN=${PYTHON:-python3}
VENV_DIR=${VENV_DIR:-.venv}

# Create venv if missing
if [[ ! -d "$VENV_DIR" ]]; then
  echo "[setup] Creating virtual environment in $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install deps if Streamlit not present
if ! python -c 'import streamlit' >/dev/null 2>&1; then
  echo "[setup] Installing dependencies"
  pip install --upgrade pip
  pip install -r requirements.txt
fi

# Load environment variables from .env if present
if [[ -f .env ]]; then
  echo "[env] Loading .env"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Ensure local imports resolve when running from repo root
export PYTHONPATH="${PYTHONPATH:-$(pwd)}"

PORT="${PORT:-8501}"
ADDRESS="${ADDRESS:-0.0.0.0}"

echo "[run] Streamlit on http://$ADDRESS:$PORT"
exec streamlit run app/streamlit_app.py --server.port "$PORT" --server.address "$ADDRESS"

