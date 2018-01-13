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

import security_testcase
from util import winnforum_testcase
import os,time,json,sys,logging
from OpenSSL import SSL,crypto


class SasSasSecurityTestcase(security_testcase.SecurityTestCase):
  # Tests changing the SAS UUT state must explicitly call the SasReset().

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_6(self):
    """Unrecognized root of trust certificate presented during registration.
    Checks that SAS UUT response with fatal alert with unknown_ca.
    """
    device_cert = self.getCertFilename('unrecognized_sas.cert')
    device_key = self.getCertFilename('unrecognized_sas.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_7(self):
    """Corrupted certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('corrupted_sas_server.cert')
    device_key = self.getCertFilename('corrupted_sas_server.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_8(self):
    """Self-signed certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    server_a_cert = self.getCertFilename('self_signed_server_a.cert')
    server_a_key = self.getCertFilename('server_a.key')
    self.assertTlsHandshakeFailure(server_a_cert, server_a_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_9(self):
    """Non-CBRS trust root signed certificate presented
    Checks that SAS UUT response with fatal alert message.
    """
    server_a_cert = self.getCertFilename('non_cbrs_signed_server_a.cert')
    server_a_key = self.getCertFilename('non_cbrs_signed_server_a.key')
    self.assertTlsHandshakeFailure(server_a_cert, server_a_key)

 
  @winnforum_testcase
  def test_WINNF_FT_S_SSS_10(self):
    """Certificate of wrong type presented during full activity dump.
    Checks that SAS UUT response with fatal alert message and HTTP status code is 403.
    """
    device_cert = self.getCertFilename('sas_ca_signed_sas_server.cert')
    device_key = self.getCertFilename('server_a.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_11(self):
    """Blacklisted certificate presented by SAS Test Harness.Checks that SAS UUT response with fatal alert message."""

    #Blacklist certificate
    config = json.load(
      open(os.path.join('testcases', 'configs', 'test_WINNF_FT_S_SSS_11', 'default.config')))
    logging.debug("FQDN value of SSS:%s " % config['fqdn'])
    self._sas_admin.BlacklistSASByFQDN({'fqdn': config['fqdn']})
    device_cert = self.getCertFilename('blacklisted_sas.cert')
    device_key = self.getCertFilename('blacklisted_sas.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)


  @winnforum_testcase
  def test_WINNF_FT_S_SSS_12(self):
    """Expired certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('sas_server_a_expired.cert')
    device_key = self.getCertFilename('sas_server_a_expired.key')

    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_13(self):
    """ Disallowed TLS method attempted during registration .
        Checks that SAS UUT response with fatal alert message below
        The SAS UUT sends a fatal alert message with the following parameters:
         AlertLevel = 2 (fatal) --> tlsv1 alert protocol version
         The SAS UUT immediately terminates the TLS session
    """
    server_a_cert = self.getCertFilename('server_a.cert')
    server_a_key = self.getCertFilename('server_a.key')
    self.assertTlsHandshakeFailure(server_a_cert, server_a_key,ciphers='CAMELLIA128-SHA',\
                                     ssl_method=SSL.TLSv1_1_METHOD)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_14(self):
    """Invalid ciphersuite presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('server_a.cert')
    device_key = self.getCertFilename('server_a.key')

    self.assertTlsHandshakeFailure(device_cert, device_key,ciphers='ECDHE-RSA-AES256-GCM-SHA384')

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_15(self):
    """Certificate with inapplicable fields presented during full activity dump. The HTTP status code is 403."""

    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})

    device_a_cert = self.getCertFilename('sas_server_inapplicable.cert')
    device_a_key = self.getCertFilename('server_a.key')


  @winnforum_testcase
  def test_WINNF_FT_S_SSS_16(self):
    """
    Certificate signed by a revoked CA presented during registration.
    """
    device_cert = os.path.join('certs', 'server_a.cert')
    device_key = os.path.join('certs', 'server_a.key')
    ca_cert = os.path.join('certs', 'WINNF_FT_S_SSS_16_sas_ca.cert')
    self.assertTlsHandshakeFailure(device_cert, device_key, ca_cert=ca_cert)


  @winnforum_testcase
  def test_WINNF_FT_S_SSS_17(self):
    """Unrecognized SAS server A certificate presented during registration.
    Checks that SAS UUT response with fatal alert with unknown_ca.
    """
    device_cert = self.getCertFilename('unrecognized_server_a.cert')
    device_key = self.getCertFilename('unrecognized_server_a.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)


  @winnforum_testcase
  def test_WINNF_FT_S_SSS_18(self):
    """
    Security requirement for Full Activity Dump message request
    """
    device_cert = self.getCertFilename('corrupted_sas_server.cert')
    device_key = self.getCertFilename('corrupted_sas_server.key')

    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    cbsd_ids = self.assertRegistered([device_a])
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    #self.assertEqual(response['response']['responseCode'], 200)
    self.assertTrue('grantId' in response)
    self.assertEqual(response['channelType'], 'GAA')
    self._sas_admin.TriggerFullActivityDump()
    response = self._sas.GetFullActivityDump()
    self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
    response = self._sas.RetrieveDumpFile(device_cert,device_key,cbsd_dump_files[0]['url'])    
    self.assertEqual(data['response']['responseCode'],401)


