#!/usr/bin/env bash
set -euo pipefail
pip install -r requirements.txt
exec uvicorn main:app --host 0.0.0.0 --port 8000
