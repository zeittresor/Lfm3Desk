import datetime
import importlib.util
from pathlib import Path
import ssl
import sys
import tempfile
import threading
import types
import unittest
import urllib.error
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import secure_http

class SecureHttpTests(unittest.TestCase):
 def tearDown(self):secure_http.tls_context.cache_clear()
 def test_context_requires_certificate_and_hostname(self):
  secure_http.tls_context.cache_clear()
  context=secure_http.tls_context()
  self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED);self.assertTrue(context.check_hostname)
 def test_windows_native_store_plus_bundle(self):
  secure_http.tls_context.cache_clear();context=Mock();factory=Mock(return_value=context)
  with patch.object(sys,'platform','win32'),patch.dict(sys.modules,{'truststore':types.SimpleNamespace(SSLContext=factory)}):
   result=secure_http.tls_context()
  factory.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT);context.load_verify_locations.assert_called_once()
  self.assertEqual(result.verify_mode,ssl.CERT_REQUIRED);self.assertTrue(result.check_hostname)
 def test_urlopen_receives_verifying_context(self):
  context=secure_http.tls_context()
  with patch('urllib.request.urlopen') as request:secure_http.open_url('https://example.com',timeout=7)
  request.assert_called_once_with('https://example.com',timeout=7,context=context)
 def test_invalid_certificate_never_retries_unverified(self):
  error=urllib.error.URLError(ssl.SSLCertVerificationError('invalid certificate'))
  with patch('urllib.request.urlopen',side_effect=error) as request:
   with self.assertRaises(urllib.error.URLError):secure_http.open_url('https://example.com')
  self.assertEqual(request.call_count,1)
 @unittest.skipUnless(importlib.util.find_spec('cryptography'),'cryptography needed for local TLS fixture')
 def test_real_tls_rejects_untrusted_then_accepts_trusted_certificate(self):
  from cryptography import x509
  from cryptography.hazmat.primitives import hashes,serialization
  from cryptography.hazmat.primitives.asymmetric import rsa
  from cryptography.x509.oid import NameOID
  from http.server import HTTPServer,BaseHTTPRequestHandler
  key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
  name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'localhost')]);now=datetime.datetime.now(datetime.timezone.utc)
  certificate=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1)).not_valid_after(now+datetime.timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]),critical=False).add_extension(x509.BasicConstraints(ca=True,path_length=None),critical=True).sign(key,hashes.SHA256()))
  class Handler(BaseHTTPRequestHandler):
   def do_GET(self):self.send_response(200);self.end_headers();self.wfile.write(b'verified')
   def log_message(self,*args):pass
  with tempfile.TemporaryDirectory() as temp:
   cert=Path(temp)/'cert.pem';private=Path(temp)/'key.pem';cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM));private.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.TraditionalOpenSSL,serialization.NoEncryption()))
   server=HTTPServer(('127.0.0.1',0),Handler);context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,private);server.socket=context.wrap_socket(server.socket,server_side=True)
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f'https://localhost:{server.server_port}/'
   try:
    with self.assertRaises(urllib.error.URLError):secure_http.open_url(url,timeout=3)
    trusted=ssl.create_default_context(cafile=str(cert))
    with patch('secure_http.tls_context',return_value=trusted):
     with secure_http.open_url(url,timeout=3) as response:self.assertEqual(response.read(),b'verified')
     with self.assertRaises(urllib.error.URLError):secure_http.open_url(url.replace('localhost','127.0.0.1'),timeout=3)
   finally:server.shutdown();server.server_close();thread.join(timeout=3)
