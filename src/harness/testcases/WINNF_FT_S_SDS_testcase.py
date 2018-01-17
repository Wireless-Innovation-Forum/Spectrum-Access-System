#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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
from util import winnforum_testcase,countdown
import os,time,json,sys,logging
from OpenSSL import SSL,crypto

class SasDomainproxySecurityTestcase(security_testcase.SecurityTestCase):

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_6(self):
    """Unrecognized root of trust certificate presented during registration
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('unrecognized_dp.cert')
    device_key = self.getCertFilename('unrecognized_dp.key')

    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_7(self):
    """Corrupted certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('corrupted_dp.cert')
    device_key = self.getCertFilename('corrupted_dp.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_8(self):
    """Self-signed certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('self_signed_dp_client.cert')
    device_key = self.getCertFilename('dp_client.key')

    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_9(self):
    """Non-CBRS trust root signed certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('non_cbrs_signed_dp.cert')
    device_key = self.getCertFilename('non_cbrs_signed_dp.key')

    self.assertTlsHandshakeFailure(device_cert, device_key)


  @winnforum_testcase
  def test_WINNF_FT_S_SDS_10(self):
    """Certificate of wrong type presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('wrong_type_dp_client.cert')
    device_key = self.getCertFilename('server.key')
    try :
      self.assertTlsHandshakeFailure(device_cert, device_key)
    except AssertionError :
      self.SasReset()
    # Load Devices
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Register the devices
    devices = [device_a]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request,device_cert, device_key)['registrationResponse']
    self.assertEqual(response[0]['response']['responseCode'], 104)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_11(self):
    """Blacklisted Certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    #Blacklist certificate
    config = json.load(
      open(os.path.join('testcases', 'configs', 'test_WINNF_FT_S_SDS_11', 'default.config')))
    logging.debug("FRN value of DP:%s " % config['frn'])
    self._sas_admin.BlacklistDPByFRN({'frn': config['frn']})

    device_cert = self.getCertFilename('blacklisted_dp.cert')
    device_key = self.getCertFilename('blacklisted_dp.key')

    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_12(self):
    """Expired certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('dp_expired.cert')
    device_key = self.getCertFilename('dp_expired.key')

    self.assertTlsHandshakeFailure(device_cert, device_key)

  def test_WINNF_FT_S_SDS_13(self):
   """ Disallowed TLS method attempted during registration .
   Checks that SAS UUT response with fatal alert message below
   The SAS UUT sends a fatal alert message with the following parameters:
   AlertLevel = 2 (fatal) --> tlsv1 alert protocol version
   The SAS UUT immediately terminates the TLS session
   """
   device_cert = self.getCertFilename('dp_client.cert')
   device_key = self.getCertFilename('dp_client.key')

   self.assertTlsHandshakeFailure(device_cert, device_key, ciphers='CAMELLIA128-SHA',\
                                        ssl_method=SSL.TLSv1_1_METHOD)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_14(self):
    """Invalid ciphersuite presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('dp_client.cert')
    device_key = self.getCertFilename('dp_client.key')

    self.assertTlsHandshakeFailure(device_cert, device_key,ciphers='ECDHE-RSA-AES256-GCM-SHA384')

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_15(self):
    """Certificate with inapplicable fields presented during registration. The response should be 104."""

    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})

    device_a_cert = self.getCertFilename('dp_client_inapplicable.cert')
    device_a_key = self.getCertFilename('dp_client.key')
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request,device_a_cert,device_a_key)['registrationResponse'][0]
                                                           
    # Check registration response
    self.assertTrue('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 104)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_16(self):
    """
    Certificate signed by a revoked CA presented during registration.
    """
    device_cert = self.getCertFilename('dp_client.cert')
    device_key = self.getCertFilename('dp_client.key')
    ca_cert = self.getCertFilename('WINNF_FT_S_SDS_16_ca.cert')
    self.assertTlsHandshakeFailure(device_cert, device_key, ca_cert=ca_cert)


  @winnforum_testcase
  def test_WINNF_FT_S_SDS_17(self):

    """
    Invalid certificate following an approved registration request
    """

    device_cert = self.getCertFilename('short_lived_dp_client.cert')
    device_key = self.getCertFilename('short_lived_dp_client.key')
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, \
                                   ['AES128-GCM-SHA256'],device_cert, device_key)

    logging.info("TLS Handshake is success")

    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    with security_testcase.CiphersOverload(self._sas, ['AES128-GCM-SHA256'], device_cert, device_key):
      self.assertRegistered([device_a])

    logging.info("device_a is in Registered State")
    
    config = json.load(
      open(os.path.join('testcases', 'configs', 'test_WINNF_FT_S_SDS_17', 'default.config')))
    logging.info("Wait timer configured to invalidate the certificate:%s secs" % config['wait_timer'])
    countdown(config['wait_timer'])
    logging.info("re-establish TLS Session")
    self.assertTlsHandshakeFailure(device_cert, device_key)



  @winnforum_testcase
  def test_WINNF_FT_S_SDS_18(self):
    """
    Invalid certificate following an approved registration request
    """
    device_cert = self.getCertFilename('short_lived_dp_client.cert')
    device_key = self.getCertFilename('short_lived_dp_client.key')
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, \
                                   ['AES128-GCM-SHA256'], device_cert, device_key)
    logging.info("TLS Handshake is success")

    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    with security_testcase.CiphersOverload(self._sas, ['AES128-GCM-SHA256'], device_cert, device_key):
      cbsd_ids,grant_ids = self.assertRegisteredAndGranted([device_a],[grant_0])

    logging.info("device_a is in Granted State")

    config = json.load(
      open(os.path.join('testcases', 'configs', 'test_WINNF_FT_S_SDS_18', 'default.config')))
    logging.debug("Wait timer configured to invalidate the certificate:%s secs" % config['wait_timer'])
    countdown(config['wait_timer'])
    logging.info("re-establish TLS Session")
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_19(self):

    """
    Invalid certificate following an approved registration request
    """
    device_cert = self.getCertFilename('short_lived_dp_client.cert')
    device_key = self.getCertFilename('short_lived_dp_client.key')
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, \
                                   ['AES128-GCM-SHA256'], device_cert, device_key)
    logging.info("TLS Handshake is success")

    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))


    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    with security_testcase.CiphersOverload(self._sas, ['AES128-GCM-SHA256'], device_cert, device_key):
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted([device_a],[grant_0])
      operation_states = [('GRANTED')]
      transfer_expiry_timers = self.assertHeartbeatsSuccessful(cbsd_ids,grant_ids,operation_states)

    logging.info("device_a is in HeartBeat Succesful State")

    config = json.load(
      open(os.path.join('testcases', 'configs', 'test_WINNF_FT_S_SDS_19', 'default.config')))
    logging.debug("Wait timer configured to invalidate the certificate:%s secs" % config['wait_timer'])
    countdown(config['wait_timer'])
    logging.info("re-establish TLS Session")
    self.assertTlsHandshakeFailure(device_cert, device_key)
 
