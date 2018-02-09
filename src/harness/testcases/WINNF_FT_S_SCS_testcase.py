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
import security_testcase
from OpenSSL import SSL
from util import winnforum_testcase,configurable_testcase, writeConfig,loadConfig

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

  def generate_SCS_12_default_config(self, filename):
    """Generates the WinnForum configuration for SCS.12"""
    # Create the actual config for client cert/key path
    
    config = { 
        'clientCert': self.getCertFilename("client_expired.cert"),
        'clientKey':self.getCertFilename("client_expired.key")
    }
    writeConfig(filename, config)
  
  @configurable_testcase(generate_SCS_12_default_config)
  def test_WINNF_FT_S_SCS_12(self,config_filename):
    """Expired certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['client_cert_path'],
                                   client_key=config['client_key_path'])

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_13(self):
    """ Disallowed TLS method attempted during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.assertTlsHandshakeFailure(ssl_method=SSL.TLSv1_1_METHOD)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_14(self):
    """Invalid ciphersuite presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.assertTlsHandshakeFailure(ciphers='ECDHE-RSA-AES256-GCM-SHA384')

  def generate_SCS_15_default_config(self, filename):
    """ Generates the WinnForum configuration for SCS.15 """
    # Create the actual config for client cert/key path
    
    config = {
        'clientCert': self.getCertFilename("client_inapplicable.cert"),
        'clientKey': self.getCertFilename("client.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_15_default_config)
  def test_WINNF_FT_S_SCS_15(self,config_filename):
    """Certificate with inapplicable fields presented during registration. 
    
    Checks that SAS UUT response with tls connection succedded and response should be 104.    
    """
    self.SasReset()
    config = loadConfig(config_filename)
    
    # load device certs and device_a from config file
    device_a_cert = config['client_cert_path']
    device_a_key = config['client_key_path']
    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    
    # Inject fccId and userId
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    self.assertTlsHandshakeFailure(client_cert=device_a_cert,client_key=device_a_key)
    
    # Send registration Request with certs(inapplicable fields) to SAS UUT 
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request,ssl_cert=device_a_cert,ssl_key=device_a_key)['registrationResponse'][0]

    # Check registration response
    self.assertEqual(response['response']['responseCode'],104)
