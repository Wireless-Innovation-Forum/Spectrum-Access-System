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

import json

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
        Checks that SAS UUT response with fatal alert message.
    """
    device_cert = self.getCertFilename('client.cert')
    device_key = self.getCertFilename('client.key')
    self.assertTlsHandshakeFailure(device_cert, device_key,ssl_method=SSL.TLSv1_1_METHOD)

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
    
    self.SasReset() 
    
    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})

    device_a_cert = self.getCertFilename('client_inapplicable.cert')
    device_a_key = self.getCertFilename('client.key')
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request,device_a_cert,device_a_key)['registrationResponse'][0]

    # Check registration response
    
    self.assertEqual(response['response']['responseCode'], 104)

    
    
  @winnforum_testcase
  def test_WINNF_FT_S_SCS_16(self):
    """
    Certificate signed by a revoked CA presented during registration.
    """
    device_cert = self.getCertFilename('client.cert')
    device_key = self.getCertFilename('client.key')
    
    self.assertTlsHandshakeFailure(device_cert, device_key)


  @winnforum_testcase
  def test_WINNF_FT_S_SCS_20(self):
    """ SAS Certificate Validation
          The SAS UUT provided certificate has the following valid parameters:
            Issuer matches a WInnForum approved SAS Provider CA
            Subject is consistent with the SAS UUT
            etc...
    """
    device_cert = self.getCertFilename('client.cert')
    device_key = self.getCertFilename('client.key')
    self.assertVerifyServerCertificateSuceed(self._sas_admin._base_url,['AES128-GCM-SHA256'],device_cert, device_key)





