#!/usr/bin/env python3
"""Servidor local do espelho, sem dependências externas."""
import argparse
import json
import math
import os
from pathlib import Path
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from urllib.parse import urlsplit
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / 'config.json'
LOCK = Lock()
DEFAULT = {
    'nome': 'Você', 'cidade': 'São Paulo', 'latitude': -23.5505,
    'longitude': -46.6333, 'fuso': 'America/Sao_Paulo',
    'mensagens': ['Hoje é um bom dia para começar.', 'Cuide de você. O resto vem depois.'],
    'agenda': [],
}


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Configuração deve ser um objeto.')
    result = {}
    for key in ('nome', 'cidade', 'fuso'):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > 100:
            raise ValueError(f'{key}: informe um texto de até 100 caracteres.')
        result[key] = value.strip()
    try:
        ZoneInfo(result['fuso'])
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError('Fuso inválido. Use, por exemplo, America/Sao_Paulo.')
    for key, limit in (('latitude', 90), ('longitude', 180)):
        value = data.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > limit:
            raise ValueError(f'{key} inválida.')
        result[key] = value
    messages = data.get('mensagens')
    if not isinstance(messages, list) or len(messages) > 30 or any(not isinstance(m, str) or len(m) > 250 for m in messages):
        raise ValueError('Use até 30 mensagens de até 250 caracteres.')
    result['mensagens'] = [m.strip() for m in messages if m.strip()]
    agenda = data.get('agenda')
    if not isinstance(agenda, list) or len(agenda) > 100:
        raise ValueError('Use até 100 compromissos.')
    result['agenda'] = []
    for item in agenda:
        if not isinstance(item, dict) or not isinstance(item.get('titulo'), str) or not 1 <= len(item['titulo'].strip()) <= 150:
            raise ValueError('Cada compromisso precisa de um título de até 150 caracteres.')
        try:
            date = item['data']
            if not isinstance(date, str) or len(date) != 16:
                raise ValueError()
            datetime.strptime(date, '%Y-%m-%dT%H:%M')
        except (KeyError, ValueError, TypeError):
            raise ValueError('Data inválida: use AAAA-MM-DDTHH:MM.')
        result['agenda'].append({'titulo': item['titulo'].strip(), 'data': date})
    return result


def read_config():
    with LOCK:
        return validate(json.loads(CONFIG.read_text('utf-8'))) if CONFIG.exists() else dict(DEFAULT)


def save_config(data):
    data = validate(data)
    with LOCK:
        fd, name = tempfile.mkstemp(dir=CONFIG.parent, prefix='.config-', suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
            os.replace(name, CONFIG)
        finally:
            Path(name).unlink(missing_ok=True)
    return data


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'static'), **kwargs)

    def json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/config':
            try:
                self.json_response(read_config())
            except (ValueError, OSError) as exc:
                self.json_response({'erro': f'Não foi possível ler config.json: {exc}'}, 500)
        elif path == '/api/health':
            self.json_response({'status': 'ok'})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != '/api/config':
            self.json_response({'erro': 'Rota não encontrada.'}, 404)
            return
        # Impede gravações de outros sites no serviço local (incluindo DNS rebinding).
        host = self.headers.get('Host', '')
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        origin = self.headers.get('Origin')
        if host not in allowed or (origin and origin != f'http://{host}'):
            self.json_response({'erro': 'Origem não permitida.'}, 403)
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 65536:
                raise ValueError('Tamanho inválido (máximo 64 KB).')
            data = json.loads(self.rfile.read(size))
            self.json_response(save_config(data))
        except (ValueError, UnicodeDecodeError) as exc:
            self.json_response({'erro': str(exc)}, 400)
        except OSError:
            self.json_response({'erro': 'Não foi possível salvar a configuração no disco.'}, 500)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Espelho: http://127.0.0.1:{args.port} | Configuração: /config.html', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
