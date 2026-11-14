#!/usr/bin/env python3
"""Espelho Touch: servidor local, persistência e ponte USB/ESP32-CAM."""
import argparse
import copy
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import tempfile
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = {'nome': 'Você', 'cidade': 'São Paulo', 'latitude': -23.5505,
            'longitude': -46.6333, 'fuso': 'America/Sao_Paulo',
            'mensagens': ['Seu tempo merece cuidado.', 'Um novo dia, novas possibilidades.'],
            'agenda': [], 'repouso': False}


def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text('utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())


def validate_config(data):
    if not isinstance(data, dict):
        raise ValueError('Configuração inválida.')
    result = {}
    for key in ['nome', 'cidade', 'fuso']:
        value = data.get(key)
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 100:
            raise ValueError(f'{key}: use de 1 a 100 caracteres.')
        result[key] = value.strip()
    try:
        ZoneInfo(result['fuso'])
    except (KeyError, ValueError):
        raise ValueError('Fuso inválido; exemplo: America/Sao_Paulo.')
    for key, limit in [('latitude', 90), ('longitude', 180)]:
        value = data.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > limit:
            raise ValueError(f'{key} inválida.')
        result[key] = value
    messages = data.get('mensagens')
    if not isinstance(messages, list) or len(messages) > 30 or any(not isinstance(m, str) or len(m) > 250 for m in messages):
        raise ValueError('Use até 30 mensagens de até 250 caracteres.')
    result['mensagens'] = [m.strip() for m in messages if m.strip()]
    events = data.get('agenda')
    if not isinstance(events, list) or len(events) > 100:
        raise ValueError('Use até 100 compromissos.')
    result['agenda'] = []
    for item in events:
        if not isinstance(item, dict) or not isinstance(item.get('titulo'), str) or not 1 <= len(item['titulo'].strip()) <= 150:
            raise ValueError('Compromisso sem título válido.')
        date = item.get('data')
        try:
            if not isinstance(date, str) or len(date) != 16:
                raise ValueError()
            datetime.strptime(date, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            raise ValueError('Data inválida: use AAAA-MM-DDTHH:MM.')
        result['agenda'].append({'titulo': item['titulo'].strip(), 'data': date})
    if not isinstance(data.get('repouso'), bool):
        raise ValueError('Repouso deve ser verdadeiro ou falso.')
    result['repouso'] = data['repouso']
    return result


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()

    def read(self):
        with self.lock:
            return validate_config(json.loads(self.path.read_text('utf-8'))) if self.path.exists() else copy.deepcopy(DEFAULTS)

    def write(self, value):
        value = validate_config(value)
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(dir=self.path.parent, prefix='.settings-')
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                    json.dump(value, stream, ensure_ascii=False, indent=2)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            finally:
                Path(temporary).unlink(missing_ok=True)
        return value


class Hardware:
    def __init__(self, demo=False):
        self.demo = demo
        self.lock = threading.Lock()
        self.connection = None
        self.last = 0
        self.telemetry = {}
        self.error = 'Não conectado'
        self.stop = threading.Event()
        self.demo_led = 0
        self.demo_mode = 'auto'

    def start(self):
        if not self.demo:
            threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        port = os.environ.get('SERIAL_PORT', '')
        if not port:
            self.error = 'Configure SERIAL_PORT no arquivo .env.'
            return
        try:
            import serial
        except ImportError:
            self.error = 'Instale requirements.txt para usar o Arduino.'
            return
        while not self.stop.is_set():
            connection = None
            try:
                connection = serial.Serial(port, int(os.environ.get('SERIAL_BAUD', '115200')), timeout=1, write_timeout=2)
                with self.lock:
                    self.connection = connection
                while not self.stop.is_set():
                    raw = connection.readline(1024)
                    if not raw or not raw.endswith(b'\n'):
                        continue
                    try:
                        data = json.loads(raw)
                        if data.get('type') != 'telemetry' or data.get('mode') not in ('auto', 'manual'):
                            continue
                        for key, low, high in [('temp_c', -40, 85), ('humidity', 0, 100), ('light_raw', 0, 1023), ('led', 0, 255)]:
                            value = data.get(key)
                            if value is None and key in ('temp_c', 'humidity'):
                                continue
                            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                                raise ValueError('Telemetria inválida')
                        if not isinstance(data.get('presence'), bool):
                            continue
                        with self.lock:
                            self.telemetry = data
                            self.last = time.monotonic()
                            self.error = ''
                    except (ValueError, AttributeError, UnicodeDecodeError):
                        continue
            except (OSError, ValueError) as exc:
                self.error = f'Falha na conexão USB ({type(exc).__name__}).'
            finally:
                with self.lock:
                    self.connection = None
                if connection:
                    connection.close()
            self.stop.wait(3)

    def state(self):
        if self.demo:
            return {'connected': True, 'demo': True, 'error': '', 'age_s': 0,
                    'telemetry': {'temp_c': 24.5, 'humidity': 58, 'presence': True,
                                  'light_raw': 420, 'led': self.demo_led, 'mode': self.demo_mode}}
        with self.lock:
            age = time.monotonic() - self.last if self.last else None
            connected = self.connection is not None and age is not None and age < 8
            return {'connected': connected, 'demo': False, 'age_s': round(age, 1) if age is not None else None,
                    'error': '' if connected else self.error or 'Sem telemetria recente do Arduino.',
                    'telemetry': copy.deepcopy(self.telemetry) if connected else {}}

    def light(self, value):
        if not isinstance(value, dict) or value.get('mode') not in ('auto', 'manual') or type(value.get('value')) is not int or not 0 <= value['value'] <= 255:
            raise ValueError('Informe mode auto/manual e value inteiro de 0 a 255.')
        if self.demo:
            self.demo_led, self.demo_mode = value['value'], value['mode']
            return {'status': 'simulado'}
        with self.lock:
            if self.connection is None or time.monotonic() - self.last > 8:
                raise ConnectionError('Arduino indisponível; comando não enviado.')
            try:
                self.connection.write((json.dumps({'cmd': 'light', **value}) + '\n').encode())
            except OSError:
                raise ConnectionError('Falha no envio ao Arduino.')
        return {'status': 'enviado', 'nota': 'Aguarde a telemetria para confirmar o valor aplicado.'}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def snapshot():
    base = os.environ.get('CAMERA_URL', '').rstrip('/')
    key = os.environ.get('CAMERA_KEY', '')
    parsed = urlsplit(base)
    if parsed.scheme != 'http' or not parsed.hostname or parsed.path or parsed.query or parsed.username or parsed.fragment or len(key) < 32:
        raise ConnectionError('Configure CAMERA_URL e CAMERA_KEY no .env e no ESP32-CAM.')
    request = Request(base + '/capture', headers={'X-Camera-Key': key})
    with build_opener(NoRedirect()).open(request, timeout=8) as response:
        content = response.read(512 * 1024 + 1)
        if response.headers.get_content_type() != 'image/jpeg' or not content.startswith(b'\xff\xd8') or len(content) > 512 * 1024:
            raise ConnectionError('Resposta inválida da câmera.')
        return content


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'app/static'), **kwargs)

    def reply(self, value, status=200, content_type='application/json; charset=utf-8'):
        body = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        try:
            if path == '/api/health':
                self.reply({'status': 'ok'})
            elif path == '/api/config':
                self.reply(self.server.store.read())
            elif path == '/api/state':
                self.reply(self.server.hardware.state())
            else:
                super().do_GET()
        except (ValueError, OSError) as exc:
            self.reply({'error': f'Falha na configuração: {type(exc).__name__}'}, 500)

    def do_POST(self):
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin')
        if host not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}') or (origin and origin != 'http://' + host):
            self.reply({'error': 'Origem não permitida.'}, 403)
            return
        if self.path not in ('/api/config', '/api/light', '/api/camera'):
            self.reply({'error': 'Rota inexistente.'}, 404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                raise ValueError('Corpo inválido (máximo 64 KB).')
            value = json.loads(self.rfile.read(length))
            if self.path == '/api/config':
                self.reply(self.server.store.write(value))
            elif self.path == '/api/light':
                self.reply(self.server.hardware.light(value))
            else:
                if value != {'confirm': True}:
                    raise ValueError('Confirme a captura pelo botão da câmera.')
                self.reply(snapshot(), content_type='image/jpeg')
        except (ValueError, UnicodeDecodeError) as exc:
            self.reply({'error': str(exc)}, 400)
        except (ConnectionError, OSError):
            self.reply({'error': 'Dispositivo indisponível. Confira alimentação, cabo, endereço e chave no .env.'}, 503)


def create_server(port=8000, demo=False, data_path=None):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.store = Store(data_path or ROOT / 'data/settings.json')
    server.hardware = Hardware(demo)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--demo', action='store_true', help='Simula sensores, sem acionar dispositivos.')
    args = parser.parse_args()
    load_env()
    server = create_server(args.port, args.demo)
    server.hardware.start()
    print(f'Espelho Touch em http://127.0.0.1:{args.port} | simulação: {args.demo}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.hardware.stop.set()
        server.server_close()


if __name__ == '__main__':
    main()
