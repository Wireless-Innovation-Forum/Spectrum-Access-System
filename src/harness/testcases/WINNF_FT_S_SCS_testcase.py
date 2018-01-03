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
import os

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

    Checks that SAS UUT response satisfy cipher security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doTestCipher('AES256-GCM-SHA384')

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_3(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy cipher security conditions.
    Checks that a CBSD registration with this configuration succeed.
    Note that the test require a SAS UUT
    """
    self.doTestCipher('ECDHE-ECDSA-AES128-GCM-SHA256')

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_4(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy cipher security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doTestCipher('ECDHE-ECDSA-AES256-GCM-SHA384')

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_5(self):
    """New registration with TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy cipher security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doTestCipher('ECDHE-RSA-AES128-GCM-SHA256')

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_6(self):
    """Unrecognized root of trust certificate presented during registration.
    Checks that SAS UUT responds with fatal alert with unknown_ca.
    """
    device_cert = os.path.join('certs', 'unrecognized_device.cert')
    device_key = os.path.join('certs', 'unrecognized_device.key')
    self.assertTlsHandshakeFailure(device_cert, device_key, alert_reason='tlsv1 alert unknown ca')

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_7(self):
    """Corrupted certificate presented during registration.
    Checks that SAS UUT responds with fatal alert message.
    """
    with open(os.path.join('certs', 'client.cert')) as f:
      data = "".join(f.read().split('-----END CERTIFICATE-----'))
    def corrupt_signature(cert, offset):
      temp = list(cert)
      temp[len(cert) - offset] = chr(ord(temp[len(cert) - offset ]) + 1)
      return ''.join(temp).strip() + '\n-----END CERTIFICATE-----\n'
    with open(os.path.join('certs', 'corrupted_client.cert'),mode='w') as f:
      f.write(corrupt_signature(data, 10))

    device_cert = os.path.join('certs', 'corrupted_client.cert')
    device_key = os.path.join('certs', 'client.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_8(self):
    """Self-signed certificate presented during registration.
    Checks that SAS UUT responds with fatal alert message.
    """
    device_cert = os.path.join('certs', 'self_signed_client.cert')
    device_key = os.path.join('certs', 'client.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_9(self):
    """Non-CBRS trust root signed certificate presented during registration.
    Checks that SAS UUT responds with fatal alert message.
    """
    device_cert = os.path.join('certs', 'non_cbrs_signed_device.cert')
    device_key = os.path.join('certs', 'non_cbrs_signed_device.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_10(self):
    """Certificate of wrong type presented during registration.
    Checks that SAS UUT responds with fatal alert message.
    """
    device_cert = os.path.join('certs', 'sas_ca_signed_client.cert')
    device_key = os.path.join('certs', 'client.key')
    self.assertTlsHandshakeFailure(device_cert, device_key)
