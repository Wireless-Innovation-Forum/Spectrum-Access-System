#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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
import json
import os
import re
import socket
import urlparse

from OpenSSL import crypto, SSL

import sas
import sas_testcase
from util import winnforum_testcase


_PEM_RE = re.compile(b"""-----BEGIN CERTIFICATE-----\r?
.+?\r?
-----END CERTIFICATE-----\r?\n?""", re.DOTALL)


# Keeps this function as module function for easy mocking to adapt to specific
# SAS implementation.
def _VerifyCertificate(certificate_content, ca_bundle_content, is_server):
  """Verifies the given certificate from the given chain store.

  Does verification described in: crypto.load_certificate(crypto.FILETYPE_PEM, match.group(0))

  Args:
    certificate_content: certificate to validate as raw file content.
    ca_bundle_content: certificate bundle content to be used as trusted CA.
    is_server: True if certificate is a server certificate, False for a
      client certificate.
  Raises:
    crypto.X509StoreContextError if certificate not valid
  """
  # is_server not used on this generic implementation...
  certificate = crypto.load_certificate(crypto.FILETYPE_PEM, certificate_content)
  store = crypto.X509Store()
  for match in _PEM_RE.finditer(ca_bundle_content):
    store.add_cert(crypto.load_certificate(crypto.FILETYPE_PEM, match.group(0)))
  store_ctx = crypto.X509StoreContext(store, certificate)
  store_ctx.verify_certificate()


class SecurityTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def assertValidClientCertificate(self, certificate_filename,
                                   ca_bundle_filename):
    with open(certificate_filename, 'rb') as f:
      certificate_data = f.read()
    with open(ca_bundle_filename) as f:
      bundle_data = f.read()
    try:
      _VerifyCertificate(certificate_data, bundle_data, False)
    except crypto.X509StoreContextError as e:
      self.fail('Invalid client certificate: ' + str(e.message))

  def assertValidServerCertificate(self, base_url):
    # Extracts servers certificate and chain.
    certificates = []
    def _ExtractCertificates(conn, cert, errnum, depth, ok):
      certificates.append(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
      return 1

    url = urlparse.urlparse('https://' + base_url)
    client = socket.socket()
    client.connect((url.hostname, url.port or 443))

    ctx = SSL.Context(SSL.TLSv1_2_METHOD)
    ctx.set_verify(SSL.VERIFY_PEER, _ExtractCertificates)

    client_ssl = SSL.Connection(ctx, client)
    client_ssl.set_connect_state()
    client_ssl.set_tlsext_host_name(url.hostname)
    try:
      client_ssl.do_handshake()
    except SSL.Error:
      pass
    client_ssl.close()

    # Checks server certificate with full chain.
    try:
      _VerifyCertificate(certificates[0], ''.join(certificates[1:]), True)
    except crypto.X509StoreContextError as e:
      self.fail('Invalid server certificate: ' + str(e.message))

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_1(self):
    """Send a registration request using a valid certificate.

    Checks that client certificate is valid.
    Checks that server certificate is valid.
    The response should be SUCCESS and includes a cbsdId.
    """
    device_cert = os.path.join('certs', 'client.cert')
    device_key = os.path.join('certs', 'client.key')

    # Checks that the client certificate is valid (checking all chain).
    self.assertValidClientCertificate(device_cert, sas.CA_CERT)

    # Does a SSL handshake only, extract the server certificate and check it.
    self.assertValidServerCertificate(self._sas_admin._base_url)

    # Registers the device with valid certificates.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request, device_cert,
                                      device_key)['registrationResponse'][0]

    # Checks registration response.
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertTrue('cbsdId' in response)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_2(self):
    """Send a registration request using an unknown certificate.

    Checks that client certificate is valid regarding unknown_ca
    and invalid regarding the SAS trusted PKI hierarchy.
    The response should be CERT_ERROR or error during TLS handshake.
    """
    device_cert = os.path.join('certs', 'unknown_device.cert')
    device_key = os.path.join('certs', 'unknown_device.key')

    # Checks that client certificate is invalid for the SAS under test.
    self.assertValidClientCertificate(device_cert,
                                      os.path.join('certs', 'unknown_ca.cert'))
    with self.assertRaises(AssertionError):
      self.assertValidClientCertificate(device_cert, sas.CA_CERT)

    # Registers the device with this unmanaged certificate.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})

    # Does a raw registration call to retrieve the HTTP code.
    request = {'registrationRequest': [device_a]}
    try:
      response = self._sas.Registration(request, device_cert, device_key)
      # Should have produced a CERT_ERROR.
      self.assertEqual(
          response['registrationResponse'][0]['response']['responseCode'], 104)
    except AssertionError as e:
      # Error during SSL handshake could be:
      # - CURLE_SSL_CONNECT_ERROR,
      # - CURLE_PEER_FAILED_VERIFICATION
      # See https://curl.haxx.se/libcurl/c/libcurl-errors.html
      ssl_code = e.args[0]
      self.assertTrue(ssl_code in (35, 51))
