#    Copyright 2018 SAS Project Authors. All Rights Reserved.
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
import os
import json
import security_testcase
from OpenSSL import SSL
from util import winnforum_testcase, configurable_testcase, writeConfig, loadConfig

SAS_CERT = os.path.join('certs', 'sas.cert')
SAS_KEY = os.path.join('certs', 'sas.key')


class SasToSasSecurityTestcase(security_testcase.SecurityTestCase):
  # Tests changing the SAS UUT state must explicitly call the SasReset().

  def generate_SSS_6_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_6"""
    # Create the actual config for sas cert/key path

    config = {
      'sasCert': self.getCertFilename("unrecognized_sas.cert"),
      'sasKey': self.getCertFilename("unrecognized_sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_6_default_config)
  def test_WINNF_FT_S_SSS_6(self, config_filename):
    """Unrecognized root of trust certificate presented during registration.

    Checks that SAS UUT response with fatal alert with unknown_ca.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_7_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_7"""
    # Create the actual config for sas cert/key path

    config = {
      'sasCert': self.getCertFilename("corrupted_sas.cert"),
      'sasKey': self.getCertFilename("corrupted_sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_7_default_config)
  def test_WINNF_FT_S_SSS_7(self,config_filename):
    """Corrupted certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_8_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_8"""
    # Create the actual config for sas cert/key path

    config = {
      'sasCert': self.getCertFilename("self_signed_sas.cert"),
      'sasKey': self.getCertFilename("sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_8_default_config)
  def test_WINNF_FT_S_SSS_8(self,config_filename):
    """Self-signed certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_9_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_9"""
    # Create the actual config for domain proxy cert/key path

    config = {
      'sasCert': self.getCertFilename("non_cbrs_signed_sas.cert"),
      'sasKey': self.getCertFilename("non_cbrs_signed_sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_9_default_config)
  def test_WINNF_FT_S_SSS_9(self,config_filename):
    """Non-CBRS trust root signed certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_10_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_10. """
    # Create the actual config for domain proxy cert/key path

    config = {
      'sasCert': self.getCertFilename("wrong_type_sas.cert"),
      'sasKey': self.getCertFilename("client.key"),
      'sasThUrl':'localhost:5000'

    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_10_default_config)
  def test_WINNF_FT_S_SSS_10(self,config_filename):
    """Certificate of wrong type presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    try:
      self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                     client_key=config['sasKey'])
    except AssertionError as e:
      self.SasReset()
      
      # Initiate Full Activity Dump
      self._sas_admin.TriggerFullActivityDump()
      try:
         self._sas.GetFullActivityDump()
      except AssertionError as e:
         # Check if HTTP status is 403
         self.assertEqual(e.args[0], 403)

  def generate_SSS_12_default_config(self, filename):
    """Generates the WinnForum configuration for SSS.12"""
    # Create the actual config for domain proxy cert/key path

    config = {
        'sasCert': self.getCertFilename("sas_expired.cert"),
        'sasKey': self.getCertFilename("sas_expired.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_12_default_config)
  def test_WINNF_FT_S_SSS_12(self,config_filename):
    """Expired certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_13(self):
    """ Disallowed TLS method attempted during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.assertTlsHandshakeFailure(SAS_CERT, SAS_KEY, ssl_method=SSL.TLSv1_1_METHOD)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_14(self):
    """Invalid ciphersuite presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.assertTlsHandshakeFailure(SAS_CERT, SAS_KEY, ciphers='ECDHE-RSA-AES256-GCM-SHA384')

  def generate_SSS_15_default_config(self, filename):
    """ Generates the WinnForum configuration for SSS.15 """
    # Create the actual config for domain proxy cert/key path

    config = {
        'sasCert': self.getCertFilename("sas_inapplicable.cert"),
        'sasKey': self.getCertFilename("sas.key"),
        'sasThUrl':'localhost:9001'
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_15_default_config)
  def test_WINNF_FT_S_SSS_15(self,config_filename):
    """Certificate with inapplicable fields presented during registration.

    Checks that SAS UUT response with tls connection succedded and response should be 104.
    """
    config = loadConfig(config_filename)

    # Load the keys/certs and check that TLS handshake is valid
    sas_cert = config['sasCert']
    sas_key = config['sasKey']
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, ['AES128-GCM-SHA256'], sas_cert, sas_key)
    
    # Initiate Full Activity Dump
    self._sas_admin.TriggerFullActivityDump() 
    try:
      self._sas.GetFullActivityDump()
    except AssertionError as e:
      # Check if HTTP status is 403
      self.assertEqual(e.args[0], 403)
