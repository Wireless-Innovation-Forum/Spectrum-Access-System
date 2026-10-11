#    Copyright 2026 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Local transport regressions using current TLS and certificate APIs."""

from datetime import datetime, timedelta, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import ssl
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import urlopen

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from jsonschema import ValidationError
from OpenSSL import SSL
import pycurl

from cert_fixture import create_certificates
import fake_sas
import request_handler
from schema_validation import validator_for
import security_testcase
from simple_crl_server import CrlHttpServer, CrlServerHttpHandler
import util


class _JsonHandler(BaseHTTPRequestHandler):
  def do_POST(self):
    body = self.rfile.read(int(self.headers['Content-Length']))
    response = json.dumps({'request': json.loads(body)}).encode('utf-8')
    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.send_header('Content-Length', str(len(response)))
    self.end_headers()
    self.wfile.write(response)

  def do_GET(self):
    response = json.dumps({'label': 'σ'}, ensure_ascii=False).encode('utf-8')
    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.send_header('Content-Length', str(len(response)))
    self.end_headers()
    self.wfile.write(response)

  def log_message(self, *_args):
    pass


class _RetryHandler(_JsonHandler):
  def do_POST(self):
    self.server.attempts = getattr(self.server, 'attempts', 0) + 1
    if self.server.attempts == 1:
      self.rfile.read(int(self.headers['Content-Length']))
      self.send_response(200)
      self.send_header('Content-Length', '1000')
      self.end_headers()
      self.wfile.write(b'{"incomplete":')
      return
    super().do_POST()


class TransportTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    directory = tempfile.TemporaryDirectory()
    cls.addClassCleanup(directory.cleanup)
    cls.directory = Path(directory.name)
    cls.certificates = create_certificates(cls.directory)
    now = datetime.now(timezone.utc)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'CRL test issuer')])
    revoked = (x509.RevokedCertificateBuilder().serial_number(42)
               .revocation_date(now - timedelta(hours=1)).build())
    cls.crl = (x509.CertificateRevocationListBuilder().issuer_name(issuer)
               .last_update(now - timedelta(hours=1))
               .next_update(now + timedelta(days=1))
               .add_revoked_certificate(revoked).sign(key, hashes.SHA256()))
    cls.crl_der = cls.crl.public_bytes(serialization.Encoding.DER)

  def start_server(self, server):
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    self.addCleanup(worker.join, 5)
    self.addCleanup(server.server_close)
    self.addCleanup(server.shutdown)
    return 'localhost:%d' % server.server_address[1]

  def start_tls_server(self, handler=_JsonHandler):
    server = HTTPServer(('localhost', 0), handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(self.certificates['server_cert'],
                            self.certificates['server_key'])
    context.load_verify_locations(self.certificates['ca'])
    context.verify_mode = ssl.CERT_REQUIRED
    context.set_ciphers('ECDHE-RSA-AES128-GCM-SHA256')
    server.socket = context.wrap_socket(server.socket, server_side=True)
    return self.start_server(server)

  def test_mutual_tls_transfers_falsey_json_and_utf8_response(self):
    base_url = self.start_tls_server()
    config = request_handler.TlsConfig()
    config.ca_cert = self.certificates['ca']
    config.client_cert = self.certificates['client_cert']
    config.client_key = self.certificates['client_key']
    for request in ({}, [], False, 0):
      with self.subTest(request=request):
        self.assertEqual(
            request_handler.RequestPost('https://' + base_url, request, config),
            {'request': request})
    self.assertEqual(request_handler.RequestGet('https://' + base_url, config),
                     {'label': 'σ'})

  def test_pyopenssl_tls_handshake_uses_current_certificate_callback(self):
    base_url = self.start_tls_server()
    testcase = security_testcase.SecurityTestCase('runTest')
    testcase._sas = SimpleNamespace(
        _tls_config=SimpleNamespace(ca_cert=self.certificates['ca']))
    self.assertTrue(testcase.doTlsHandshake(
        base_url, self.certificates['client_cert'], self.certificates['client_key'],
        ['ECDHE-RSA-AES128-GCM-SHA256'], SSL.TLSv1_2_METHOD))

  def test_failed_transfer_does_not_pollute_retry_response(self):
    base_url = self.start_tls_server(_RetryHandler)
    config = request_handler.TlsConfig()
    config.ca_cert = self.certificates['ca']
    config.client_cert = self.certificates['client_cert']
    config.client_key = self.certificates['client_key']
    with mock.patch.object(request_handler, 'REQUEST_ATTEMPT_DELAY_SECOND', 0):
      self.assertEqual(request_handler.RequestPost(
          'https://' + base_url, {'completed': True}, config),
          {'request': {'completed': True}})

  def test_mutual_tls_rejects_missing_client_certificate(self):
    base_url = self.start_tls_server()
    config = request_handler.TlsConfig()
    config.ca_cert = self.certificates['ca']
    with mock.patch.object(request_handler, 'MAX_REQUEST_ATTEMPT_COUNT', 1), \
         mock.patch.object(request_handler, 'REQUEST_ATTEMPT_DELAY_SECOND', 0):
      with self.assertRaises(pycurl.error):
        request_handler.RequestGet('https://' + base_url, config)

  def test_certificate_fingerprint_keeps_protocol_format(self):
    certificate = self.certificates['client_cert']
    cert = x509.load_pem_x509_certificate(Path(certificate).read_bytes())
    digest = hashlib.sha1(cert.public_bytes(serialization.Encoding.DER)).hexdigest()
    expected = ':'.join(digest[i:i + 2].upper() for i in range(0, len(digest), 2))
    self.assertEqual(util.getCertificateFingerprint(certificate), expected)

  def test_schema_resolves_nested_local_references(self):
    schema = Path(__file__).resolve().parents[2] / 'schema' / 'GrantRequest.schema.json'
    validator = validator_for(schema)
    frequency = {'lowFrequency': 3550000000, 'highFrequency': 3560000000}
    request = {'cbsdId': 'test-cbsd', 'operationParam': {
        'maxEirp': 30, 'operationFrequencyRange': frequency}}
    validator.validate(request)
    frequency['highFrequency'] = 'invalid'
    with self.assertRaises(ValidationError) as raised:
      validator.validate(request)
    self.assertEqual(list(raised.exception.path),
                     ['operationParam', 'operationFrequencyRange', 'highFrequency'])

  def test_fake_sas_converts_der_crl_into_ssl_trust_store(self):
    crl_path = self.directory / 'issuer.crl'
    crl_path.write_bytes(self.crl_der)
    index_path = self.directory / 'index.txt'
    index_path.write_text(crl_path.name + '\n', encoding='utf-8')
    contexts = []

    def create_context(_purpose):
      context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
      contexts.append(context)
      return context

    with mock.patch.object(fake_sas, 'HTTPServer') as server_factory, \
         mock.patch.object(fake_sas.ssl, 'create_default_context', create_context), \
         mock.patch.object(ssl.SSLContext, 'wrap_socket', return_value=mock.sentinel.socket), \
         mock.patch.object(fake_sas, 'CA_CERT', self.certificates['ca']), \
         mock.patch.object(fake_sas, 'CERT_FILE', self.certificates['server_cert']), \
         mock.patch.object(fake_sas, 'KEY_FILE', self.certificates['server_key']):
      fake_sas.RunFakeServer('v1.2', 'v1.2', False, str(index_path))
      server_factory.return_value.serve_forever.assert_called_once()
      server_factory.return_value.server_close.assert_called_once()
    self.assertEqual(contexts[0].cert_store_stats()['crl'], 1)
    self.assertEqual(contexts[0].verify_mode, ssl.CERT_REQUIRED)
    self.assertTrue(contexts[0].verify_flags & ssl.VERIFY_CRL_CHECK_CHAIN)

  def test_fake_sas_closes_server_for_invalid_or_missing_crls(self):
    invalid_crl = self.directory / 'invalid.crl'
    invalid_crl.write_bytes(b'not a DER CRL')
    for entry in ('invalid.crl', 'nonexistent.crl', None):
      with self.subTest(entry=entry):
        index = self.directory / 'invalid-index.txt'
        if entry is None:
          index.unlink(missing_ok=True)
        else:
          index.write_text(entry + '\n', encoding='utf-8')
        with mock.patch.object(fake_sas, 'HTTPServer') as server_factory:
          fake_sas.RunFakeServer('v1.2', 'v1.2', False, str(index))
          server_factory.return_value.serve_forever.assert_not_called()
          server_factory.return_value.server_close.assert_called_once()

  def test_crl_http_server_returns_der_bytes(self):
    (self.directory / 'issuer.crl').write_bytes(self.crl_der)
    base_url = self.start_server(CrlHttpServer(
        '/crl/', str(self.directory), ('localhost', 0), CrlServerHttpHandler))
    with urlopen('http://' + base_url + '/crl/issuer.crl', timeout=5) as response:
      self.assertEqual(response.headers['Content-Type'], 'application/pkix-crl')
      body = response.read()
    self.assertEqual(body, self.crl_der)
    self.assertEqual(x509.load_der_x509_crl(body)[0].serial_number, 42)

  def test_crl_http_server_sends_complete_not_found_responses(self):
    base_url = self.start_server(CrlHttpServer(
        '/crl/', str(self.directory), ('localhost', 0), CrlServerHttpHandler))
    for path in ('/wrong/issuer.crl', '/crl/../issuer.crl', '/crl/missing.crl'):
      with self.subTest(path=path):
        with self.assertRaises(HTTPError) as raised:
          urlopen('http://' + base_url + path, timeout=5)
        self.assertEqual(raised.exception.code, 404)
        raised.exception.close()


if __name__ == '__main__':
  unittest.main()
