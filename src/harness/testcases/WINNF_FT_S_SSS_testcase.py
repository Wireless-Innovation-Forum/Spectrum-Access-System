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
from OpenSSL import SSL
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
import security_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, loadConfig,\
getCertificateFingerprint

SAS_TH_URL = "https://localhost/v1.2"
class SasToSasSecurityTestcase(security_testcase.SecurityTestCase):
  # Tests changing the SAS UUT state must explicitly call the SasReset().

  def generate_SSS_6_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_6"""
    # Create the actual config for SAS cert/key path

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
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TH_URL })

    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_7_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_7"""
    # Create the actual config for SAS cert/key path

    config = {
        'sasCert': self.getCertFilename("corrupted_sas.cert"),
        'sasKey': self.getCertFilename("corrupted_sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_7_default_config)
  def test_WINNF_FT_S_SSS_7(self, config_filename):
    """Corrupted certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TH_URL })
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_8_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_8"""
    # Create the actual config for SAS cert/key path

    config = {
        'sasCert': self.getCertFilename("self_signed_sas.cert"),
        'sasKey': self.getCertFilename("sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_8_default_config)
  def test_WINNF_FT_S_SSS_8(self, config_filename):
    """Self-signed certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TH_URL })
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_9_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_9"""
    # Create the actual config for SAS cert/key path

    config = {
        'sasCert': self.getCertFilename("non_cbrs_signed_sas.cert"),
        'sasKey': self.getCertFilename("non_cbrs_signed_sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_9_default_config)
  def test_WINNF_FT_S_SSS_9(self, config_filename):
    """Non-CBRS trust root signed certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TH_URL })
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_12_default_config(self, filename):
    """Generates the WinnForum configuration for SSS.12"""
    # Create the actual config for SAS cert/key path

    config = {
        'sasCert': self.getCertFilename("sas_expired.cert"),
        'sasKey': self.getCertFilename("sas_expired.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_12_default_config)
  def test_WINNF_FT_S_SSS_12(self, config_filename):
    """Expired certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TH_URL })
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_13_default_config(self, filename):
    """Generates the WinnForum configuration for SSS.13"""
    # Create the actual config for SAS cert/key path

    config = {
        'sasCert': self.getCertFilename("sas.cert"),
        'sasKey': self.getCertFilename("sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_13_default_config)
  def test_WINNF_FT_S_SSS_13(self,config_filename):
    """ Disallowed TLS method attempted during registration.

        Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()

    # Load the configuration
    config = loadConfig(config_filename)

    # Read the fingerprint from the certificate
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TH_URL})
    self.assertTlsHandshakeFailure(config['sasCert'],
                                   config['sasKey'],
                                   ssl_method=SSL.TLSv1_1_METHOD)

  def generate_SSS_14_default_config(self, filename):
    """Generates the WinnForum configuration for SSS.14"""
    # Create the actual config for SAS cert/key path

    config = {
        'sasCert': self.getCertFilename("sas.cert"),
        'sasKey': self.getCertFilename("sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_14_default_config)
  def test_WINNF_FT_S_SSS_14(self, config_filename):
    """ Invalid cipher suite presented during registration.

        Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()

    # Load the configuration
    config = loadConfig(config_filename)

    # Read the fingerprint from the certificate
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TH_URL })
    self.assertTlsHandshakeFailure(config['sasCert'],
                                   config['sasKey'],
                                   ciphers='ECDHE-RSA-AES256-GCM-SHA384')
