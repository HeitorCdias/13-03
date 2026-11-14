#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$PROJECT_DIR" == *'%'* || "$PROJECT_DIR" == *'"'* || "$PROJECT_DIR" == *\\* || "$PROJECT_DIR" == *$'\n'* || "$PROJECT_DIR" == *$'\r'* || "$PROJECT_DIR" == *'`'* || "$PROJECT_DIR" == *'$'* ]]; then
  echo 'Use um caminho sem aspas, %, barras invertidas, cifrão, crases ou quebras de linha.' >&2
  exit 1
fi
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
SERVICE_FILE="$UNIT_DIR/espelho.service"
DESKTOP_FILE="$AUTOSTART_DIR/espelho.desktop"
if [[ -e "$SERVICE_FILE" || -e "$DESKTOP_FILE" ]]; then
  echo 'Já existe configuração do espelho. Preserve ou remova os arquivos antes de reinstalar:' >&2
  echo "$SERVICE_FILE" >&2
  echo "$DESKTOP_FILE" >&2
  exit 1
fi
command -v python3 >/dev/null
command -v systemctl >/dev/null
if ! command -v chromium >/dev/null && ! command -v chromium-browser >/dev/null; then
  echo 'Instale o Chromium antes de configurar a inicialização.' >&2
  exit 1
fi
systemctl --user show-environment >/dev/null
mkdir -p "$UNIT_DIR" "$AUTOSTART_DIR"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Servidor local do espelho inteligente
After=network.target

[Service]
Type=simple
WorkingDirectory="$PROJECT_DIR"
ExecStart=/usr/bin/env python3 "$PROJECT_DIR/server.py"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Espelho inteligente
Exec=bash "$PROJECT_DIR/scripts/quiosque.sh"
Terminal=false
EOF
systemctl --user daemon-reload
systemctl --user enable --now espelho.service
echo 'Servidor ativado. O Chromium abrirá no próximo login gráfico.'
echo 'Para abrir agora: bash scripts/quiosque.sh'
