#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -x "$PROJECT_DIR/.venv/bin/python" ]] || { echo 'Execute instalar-pi.sh primeiro.' >&2; exit 1; }
if [[ "$PROJECT_DIR" == *'%'* || "$PROJECT_DIR" == *'"'* || "$PROJECT_DIR" == *\\* || "$PROJECT_DIR" == *'$'* || "$PROJECT_DIR" == *'`'* || "$PROJECT_DIR" == *$'\n'* || "$PROJECT_DIR" == *$'\r'* ]]; then
  echo 'Use um caminho simples, sem caracteres de expansão.' >&2; exit 1
fi
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
START_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
[[ ! -e "$UNIT_DIR/espelho-touch.service" && ! -e "$START_DIR/espelho-touch.desktop" ]] || { echo 'Configuração já existe; preserve ou remova antes de reinstalar.' >&2; exit 1; }
systemctl --user show-environment >/dev/null
mkdir -p "$UNIT_DIR" "$START_DIR"
cat > "$UNIT_DIR/espelho-touch.service" <<EOF
[Unit]
Description=Espelho Touch - servidor local
After=network.target
[Service]
WorkingDirectory="$PROJECT_DIR"
ExecStart="$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/app/server.py"
Restart=on-failure
RestartSec=5
[Install]
WantedBy=default.target
EOF
cat > "$START_DIR/espelho-touch.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Espelho Touch
Exec=bash "$PROJECT_DIR/scripts/quiosque.sh"
Terminal=false
EOF
systemctl --user daemon-reload
systemctl --user enable --now espelho-touch.service
echo 'Servidor ativo. Quiosque será aberto no próximo login no desktop.'
