#!/usr/bin/env bash
set -euo pipefail
# Executar como o usuário da sessão gráfica, nunca com sudo.
BROWSER=""
for candidate in chromium chromium-browser; do
  if command -v "$candidate" >/dev/null 2>&1; then
    BROWSER="$candidate"
    break
  fi
done
if [[ -z "$BROWSER" ]]; then
  echo 'Chromium não encontrado. Instale chromium (ou chromium-browser) pelo apt.' >&2
  exit 1
fi
python3 - <<'PY'
import time
import urllib.request
for attempt in range(60):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2) as response:
            if response.status == 200:
                break
    except OSError:
        pass
    time.sleep(1)
else:
    raise SystemExit('O servidor não ficou pronto. Consulte journalctl --user -u espelho.service')
PY
if [[ "${XDG_SESSION_TYPE:-}" == "x11" ]] && command -v xset >/dev/null 2>&1; then
  xset s off || true
  xset -dpms || true
  xset s noblank || true
fi
exec "$BROWSER" --kiosk --no-first-run --noerrdialogs --disable-session-crashed-bubble http://127.0.0.1:8000/
