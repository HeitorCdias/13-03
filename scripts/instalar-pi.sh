#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
python3 -m venv .venv
.venv/bin/python -m pip install --requirement requirements.txt
if [[ ! -e .env ]]; then cp .env.example .env; fi
echo 'Dependências instaladas. Edite .env antes de usar os dispositivos.'
echo 'Teste sem hardware: .venv/bin/python app/server.py --demo'
