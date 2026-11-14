#!/usr/bin/env bash
set -euo pipefail
BROWSER=""
for candidate in chromium chromium-browser; do
  if command -v "$candidate" >/dev/null; then BROWSER="$candidate"; break; fi
done
[[ -n "$BROWSER" ]] || { echo 'Instale Chromium pelo apt.' >&2; exit 1; }
python3 - <<'PY'
import time
from urllib.request import urlopen
for attempt in range(60):
    try:
        with urlopen('http://127.0.0.1:8000/api/health', timeout=2) as response:
            if response.status == 200: break
    except OSError:
        pass
    time.sleep(1)
else:
    raise SystemExit('Servidor indisponível. Consulte o serviço espelho-touch.')
PY
if [[ "${XDG_SESSION_TYPE:-}" == x11 ]] && command -v xset >/dev/null; then
  xset s off || true
  xset -dpms || true
fi
exec "$BROWSER" --kiosk --no-first-run --noerrdialogs http://127.0.0.1:8000/
