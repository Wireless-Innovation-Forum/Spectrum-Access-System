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
from util import winnforum_testcase,countdown
import os,time,json,sys,logging
from OpenSSL import SSL,crypto


class SasCbsdSecurityTestcase(security_testcase.SecurityTestCase):
  # Tests changing the SAS UUT state must explicitly call the SasReset().

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_1(self):
    """New registration with TLS_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy cipher security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doTestCipher('AES128-GCM-SHA256')

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_2(self):
    """New registration with TLS_RSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doTestCipher('AES256-GCM-SHA384')

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_3(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a CBSD registration with this configuration succeed.
    Note that the test require a SAS UUT
    """
    self.doTestCipher('ECDHE-ECDSA-AES128-GCM-SHA256')

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_4(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doTestCipher('ECDHE-ECDSA-AES256-GCM-SHA384')

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_5(self):
    """New registration with TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doTestCipher('ECDHE-RSA-AES128-GCM-SHA256')

  @winnforum_testcase 
  def test_WINNF_FT_S_SCS_11(self):
    """Blacklisted Certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    #Blacklist certificate
    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.BlacklistByFccIdAndSerialNumber({'fccId': device_a['fccId'],'CbsdSerialNumber': device_a['cbsdSerialNumber']})
    device_cert = self.getCertFilename('device_a.cert')
    device_key = self.getCertFilename('device_a.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_12(self):
    """Expired certificate presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('client_expired.cert')
    device_key = self.getCertFilename('client_expired.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)


  @winnforum_testcase
  def test_WINNF_FT_S_SCS_13(self):
    """ Disallowed TLS method attempted during registration .
        Checks that SAS UUT response with fatal alert message below
        The SAS UUT sends a fatal alert message with the following parameters:
         AlertLevel = 2 (fatal) --> tlsv1 alert protocol version
         The SAS UUT immediately terminates the TLS session
    """
    device_cert = self.getCertFilename('client.cert')
    device_key = self.getCertFilename('client.key')
    self.assertTlsHandshakeFailure(device_cert, device_key,ciphers='CAMELLIA128-SHA',\
                                     ssl_method=SSL.TLSv1_1_METHOD)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_14(self):
    """Invalid ciphersuite presented during registration.
    Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('client.cert')
    device_key = self.getCertFilename('client.key')
    self.assertTlsHandshakeFailure(device_cert, device_key,ciphers='ECDHE-RSA-AES256-GCM-SHA384')


  @winnforum_testcase
  def test_WINNF_FT_S_SCS_15(self):
    """Certificate with inapplicable fields presented during registration. The response should be 104."""
    
    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})

    device_a_cert = self.getCertFilename('client_inapplicable.cert')
    device_a_key = self.getCertFilename('client.key')
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request,device_a_cert,device_a_key)['registrationResponse'][0]

    # Check registration response
    self.assertTrue('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 104)


  @winnforum_testcase
  def test_WINNF_FT_S_SCS_16(self):
    """
    Certificate signed by a revoked CA presented during registration.
    """
    device_cert = self.getCertFilename('client.cert')
    device_key = self.getCertFilename('client.key')
    ca_cert = self.getCertFilename('WINNF_FT_S_SCS_16_ca.cert')
    self.assertTlsHandshakeFailure(device_cert, device_key, ca_cert=ca_cert)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_17(self):
    """
    Invalid certificate following an approved registration reques
    """
    device_cert = self.getCertFilename('short_lived_client.cert')
    device_key = self.getCertFilename('short_lived_client.key')
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, \
                                   ['AES128-GCM-SHA256'],device_cert, device_key)

    logging.info("TLS Handshake is success")

    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    with security_testcase.CiphersOverload(self._sas, ['AES128-GCM-SHA256'], device_cert, device_key):
      self.assertRegistered([device_a])

    logging.info("device_a is in Registered State")
    config = json.load(
        open(os.path.join('testcases','configs','test_WINNF_FT_S_SCS_17','default.config')))
    logging.info("Wait timer configured to invalidate the certificate:%s" %config['wait_timer'])

    countdown(config['wait_timer'])

    logging.info("re-establish TLS Session")
    self.assertTlsHandshakeFailure(device_cert, device_key)


  @winnforum_testcase
  def test_WINNF_FT_S_SCS_18(self):
    """
    Invalid certificate following an approved grant request
    """
    device_cert = self.getCertFilename('short_lived_client.cert')
    device_key = self.getCertFilename('short_lived_client.key')
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
      open(os.path.join('testcases', 'configs', 'test_WINNF_FT_S_SCS_18', 'default.config')))
    logging.info("Wait timer configured to invalidate the certificate:%s secs" % config['wait_timer'])

    countdown(config['wait_timer'])
    logging.info("re-establish TLS Session")
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_19(self):

    """
    Invalid certificate following an approved heartbeat request
    """
    device_cert = self.getCertFilename('short_lived_client.cert')
    device_key = self.getCertFilename('short_lived_client.key')
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

    logging.info("device_a is in HeartBeat Successful State")

    config = json.load(
      open(os.path.join('testcases', 'configs', 'test_WINNF_FT_S_SCS_19', 'default.config')))
    logging.info("Wait timer configured to invalidate the certificate:%s secs" % config['wait_timer'])

    countdown(config['wait_timer'])
    logging.info("re-establish TLS Session")
    self.assertTlsHandshakeFailure(device_cert, device_key)

  def test_WINNF_FT_S_SCS_20(self):
    """ SAS Certificate Validation
          The SAS UUT provided certificate has the following valid parameters:
            Issuer matches a WInnForum approved SAS Provider CA
            Subject is consistent with the SAS UUT
            etc...
    """
    device_cert = self.getCertFilename('client.cert')
    device_key = self.getCertFilename('client.key')
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url,['AES128-GCM-SHA256'],device_cert, device_key,True)

