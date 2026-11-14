"""Exercita uma porta serial virtual e uma câmera HTTP local, sem placas."""
import importlib.util
import json
import os
from pathlib import Path
import select
import threading
import time
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

spec=importlib.util.spec_from_file_location('touch_bridge',Path(__file__).resolve().parents[1]/'app/server.py')
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class IntegrationTests(unittest.TestCase):
    def test_camera_header_and_jpeg_transfer(self):
        key='a'*64
        received=[]
        class Camera(BaseHTTPRequestHandler):
            def do_GET(self):
                received.append((self.path,self.headers.get('X-Camera-Key')))
                self.send_response(200)
                self.send_header('Content-Type','image/jpeg')
                self.end_headers()
                self.wfile.write(b'\xff\xd8picture\xff\xd9')
            def log_message(self,*args): pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Camera)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ,{'CAMERA_URL':f'http://127.0.0.1:{server.server_port}','CAMERA_KEY':key}):
                self.assertEqual(app.snapshot(),b'\xff\xd8picture\xff\xd9')
            self.assertEqual(received,[('/capture',key)])
        finally:
            server.shutdown();server.server_close();thread.join()

    @unittest.skipUnless(os.name=='posix' and importlib.util.find_spec('serial'),'Requer POSIX e pyserial para porta virtual')
    def test_serial_telemetry_and_light_command(self):
        import pty
        master,slave=pty.openpty()
        port=os.ttyname(slave)
        hw=app.Hardware()
        thread=threading.Thread(target=hw.run,daemon=True)
        telemetry={'type':'telemetry','temp_c':23.5,'humidity':60,'presence':True,'light_raw':420,'led':0,'mode':'auto'}
        try:
            with patch.dict(os.environ,{'SERIAL_PORT':port,'SERIAL_BAUD':'115200'}):
                thread.start()
                deadline=time.monotonic()+4
                while hw.connection is None and time.monotonic()<deadline:time.sleep(.02)
                self.assertIsNotNone(hw.connection)
                os.write(master,b'not json\n')
                os.write(master,(json.dumps(telemetry)+'\n').encode())
                while not hw.state()['connected'] and time.monotonic()<deadline:time.sleep(.02)
                self.assertEqual(hw.state()['telemetry']['temp_c'],23.5)
                self.assertEqual(hw.light({'mode':'manual','value':128})['status'],'enviado')
                ready,_,_=select.select([master],[],[],2)
                self.assertTrue(ready)
                command=json.loads(os.read(master,1024))
                self.assertEqual(command,{'cmd':'light','mode':'manual','value':128})
        finally:
            hw.stop.set();thread.join(timeout=3)
            os.close(master);os.close(slave)


if __name__=='__main__':unittest.main()
