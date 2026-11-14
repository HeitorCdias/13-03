import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

spec = importlib.util.spec_from_file_location('mirror_server', Path(__file__).resolve().parents[1] / 'server.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class MirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        app.CONFIG = Path(cls.directory.name) / 'config.json'
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.directory.cleanup()

    def request(self, path, data=None, origin=None):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        request = urllib.request.Request(self.base + path, headers=headers, data=json.dumps(data).encode() if data is not None else None)
        return urllib.request.urlopen(request, timeout=3)

    def test_dashboard_and_assets(self):
        for path in ('/', '/app.js', '/style.css', '/config.html', '/config.js', '/api/health'):
            with self.request(path) as response:
                self.assertEqual(response.status, 200)
                self.assertGreater(len(response.read()), 10)

    def test_configuration_persists_unicode_and_agenda(self):
        data = copy.deepcopy(app.DEFAULT)
        data['nome'] = 'Heitor'
        data['agenda'] = [{'titulo':'Reunião de amanhã', 'data':'2030-03-13T09:30'}]
        with self.request('/api/config', data, self.base) as response:
            self.assertEqual(json.load(response), data)
        with self.request('/api/config') as response:
            self.assertEqual(json.load(response), data)
        self.assertEqual(json.loads(app.CONFIG.read_text('utf-8')), data)

    def test_invalid_data_does_not_overwrite(self):
        original = app.read_config()
        for key, value in [('latitude', 91), ('longitude', float('nan')), ('fuso', 'invalid'), ('agenda', [{'titulo':'Erro', 'data':'2026-02-30T12:00'}]), ('mensagens', ['x'*251])]:
            with self.subTest(key=key):
                data = copy.deepcopy(app.DEFAULT)
                data[key] = value
                with self.assertRaises(urllib.error.HTTPError) as error:
                    self.request('/api/config', data)
                self.assertEqual(error.exception.code, 400)
                self.assertEqual(app.read_config(), original)

    def test_rejects_cross_origin_writes(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/config', app.DEFAULT, 'https://example.com')
        self.assertEqual(error.exception.code, 403)

    def test_config_file_not_exposed_as_static(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/config.json')
        self.assertEqual(error.exception.code, 404)


if __name__ == '__main__':
    unittest.main()
