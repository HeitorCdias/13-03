import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

spec = importlib.util.spec_from_file_location('mirror', Path(__file__).resolve().parents[1]/'app/server.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = app.create_server(0, True, Path(self.temp.name)/'settings.json')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def call(self, path, data=None, origin=None):
        headers = {'Content-Type':'application/json'}
        if origin: headers['Origin'] = origin
        request = Request(self.base+path, data=None if data is None else json.dumps(data).encode(), headers=headers)
        with urlopen(request, timeout=3) as response:
            return response.status, response.read()

    def test_assets_and_health(self):
        for route in ['/', '/app.js', '/style.css', '/api/health']:
            status, body = self.call(route)
            self.assertEqual(status, 200)
            self.assertTrue(body)

    def test_config_roundtrip_and_restart(self):
        data = copy.deepcopy(app.DEFAULTS)
        data['nome'] = 'João'
        data['agenda'] = [{'titulo':'Consulta', 'data':'2030-03-12T08:00'}]
        self.call('/api/config', data)
        self.assertEqual(json.loads(self.call('/api/config')[1]), data)
        other = app.Store(self.server.store.path)
        self.assertEqual(other.read(), data)

    def test_invalid_configuration_preserves_saved_data(self):
        self.server.store.write(app.DEFAULTS)
        for key, value in [('latitude',91),('longitude',float('nan')),('fuso','invalid'),('repouso','yes'),('mensagens',['x'*251]),('agenda',[{'titulo':'x','data':'2026-02-30T12:00'}])]:
            data = copy.deepcopy(app.DEFAULTS)
            data[key] = value
            with self.subTest(key=key), self.assertRaises(HTTPError) as error:
                self.call('/api/config',data)
            self.assertEqual(error.exception.code,400)
            self.assertEqual(self.server.store.read(),app.DEFAULTS)

    def test_origin_and_private_files(self):
        with self.assertRaises(HTTPError) as error:
            self.call('/api/config', app.DEFAULTS, 'https://example.com')
        self.assertEqual(error.exception.code,403)
        for route in ['/.env','/server.py','/data/settings.json']:
            with self.assertRaises(HTTPError) as error:
                self.call(route)
            self.assertEqual(error.exception.code,404)

    def test_demo_and_light_validation(self):
        state = json.loads(self.call('/api/state')[1])
        self.assertTrue(state['demo'])
        self.call('/api/light',{'mode':'manual','value':128})
        state=json.loads(self.call('/api/state')[1])
        self.assertEqual(state['telemetry']['led'],128)
        for value in [-1,256,True,1.5]:
            with self.assertRaises(HTTPError) as error:
                self.call('/api/light',{'mode':'manual','value':value})
            self.assertEqual(error.exception.code,400)

    def test_disconnected_hardware_does_not_fake_readings(self):
        self.server.hardware = app.Hardware(False)
        state=json.loads(self.call('/api/state')[1])
        self.assertFalse(state['connected'])
        self.assertEqual(state['telemetry'],{})
        with self.assertRaises(HTTPError) as error:
            self.call('/api/light',{'mode':'manual','value':100})
        self.assertEqual(error.exception.code,503)

    def test_camera_requires_explicit_capture_and_handles_unavailable(self):
        with self.assertRaises(HTTPError) as error:
            self.call('/api/camera',{})
        self.assertEqual(error.exception.code,400)
        with patch.dict(app.os.environ, {'CAMERA_URL':'','CAMERA_KEY':''}):
            with self.assertRaises(HTTPError) as error:
                self.call('/api/camera',{'confirm':True})
            self.assertEqual(error.exception.code,503)
        with patch.object(app, 'snapshot', return_value=b'\xff\xd8test\xff\xd9'):
            self.assertEqual(self.call('/api/camera',{'confirm':True})[1], b'\xff\xd8test\xff\xd9')

    def test_stale_telemetry_is_hidden(self):
        hw=app.Hardware()
        hw.connection=object()
        hw.telemetry={'temp_c':30}
        hw.last=app.time.monotonic()-9
        self.assertFalse(hw.state()['connected'])
        self.assertEqual(hw.state()['telemetry'],{})


if __name__ == '__main__':
    unittest.main()
