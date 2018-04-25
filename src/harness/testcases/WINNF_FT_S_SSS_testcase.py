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
import json
import logging
import os
from OpenSSL import SSL
from OpenSSL.crypto import load_certificate, FILETYPE_PEM

from request_handler import HTTPError
import security_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, loadConfig,\
getCertificateFingerprint
from request_handler import HTTPError

SAS_CERT = os.path.join('certs', 'sas.cert')
SAS_KEY = os.path.join('certs', 'sas.key')
SAS_TEST_HARNESS_URL = 'https://fake.sas.url.not.used/v1.2'

class SasToSasSecurityTestcase(security_testcase.SecurityTestCase):
  # Tests changing the SAS UUT state must explicitly call the SasReset().

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_1(self):
    """New registration with TLS_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy cipher security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('AES128-GCM-SHA256',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TEST_HARNESS_URL)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_2(self):
    """New registration with TLS_RSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('AES256-GCM-SHA384',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TEST_HARNESS_URL)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_3(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('ECDHE-ECDSA-AES128-GCM-SHA256',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TEST_HARNESS_URL)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_4(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('ECDHE-ECDSA-AES256-GCM-SHA384',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TEST_HARNESS_URL)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_5(self):
    """New registration with TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('ECDHE-RSA-AES128-GCM-SHA256',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TEST_HARNESS_URL)

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
    """Unrecognized root of trust certificate presented by SAS Test Harness.

    Checks that SAS UUT response with fatal alert with unknown_ca.
    """
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TEST_HARNESS_URL })

    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            is_sas=True)

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
    """Corrupted certificate presented by SAS Test Harness.

    Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TEST_HARNESS_URL })
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            is_sas=True)

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
    """Self-signed certificate presented by SAS Test Harness.

    Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TEST_HARNESS_URL })
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            is_sas=True)

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
    """Non-CBRS trust root signed certificate presented by SAS Test Harness.

    Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TEST_HARNESS_URL })
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            is_sas=True)

  def generate_SSS_10_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_10. """
    # Create the actual config for SAS cert/key path 

    config = {
        'sasCert': self.getCertFilename("wrong_type_sas.cert"),
        'sasKey': self.getCertFilename("client.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_10_default_config)
  def test_WINNF_FT_S_SSS_10(self, config_filename):
    """Certificate of wrong type presented during Full Activity Dump.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)

    # Reset the SAS UUT
    self.SasReset()

    # Notify SAS UUT about peer SAS
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,\
                                     'url': SAS_TEST_HARNESS_URL})
    try:
      self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                     client_key=config['sasKey'])
    except AssertionError:
      trigger_succeed = False
      try:
        self.TriggerFullActivityDumpAndWaitUntilComplete(config['sasCert'], config['sasKey'])
        trigger_succeed = True
      except HTTPError as e:
        # Check if HTTP status is 403
        self.assertEqual(e.error_code, 403)
      self.assertFalse(trigger_succeed, "Full Activity Dump is expected to fail")

  def generate_SSS_11_default_config(self, filename):
    """Generate the WinnForum configuration for SSS_11."""
    # Create the configuration for blacklisted SAS cert/key path.

    config = {
        'sasCert': self.getCertFilename("blacklisted_sas.cert"),
        'sasKey': self.getCertFilename("blacklisted_sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_11_default_config)
  def test_WINNF_FT_S_SSS_11(self, config_filename):
    """Blacklisted certificate presented by SAS Test Harness.

    Checks that SAS UUT response with fatal alert message.
    """
    # Reset SAS UUT
    self.SasReset()

    # Read the configuration
    config = loadConfig(config_filename)

    # Read the fingerprint from the certificate
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TEST_HARNESS_URL})

    # Tls handshake fails or Http 403
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            is_sas=True)

    logging.info("TLS handshake failed as the sas certificate has blacklisted")

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
    """Expired certificate presented by SAS Test Harness.

    Checks that SAS UUT response with fatal alert message.
    """
    self.SasReset()
    config = loadConfig(config_filename)
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': SAS_TEST_HARNESS_URL })
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            is_sas=True)

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
                                   'url': SAS_TEST_HARNESS_URL})
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            ssl_method=SSL.TLSv1_1_METHOD,
                                            is_sas=True)

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
                                   'url': SAS_TEST_HARNESS_URL })
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            ciphers='ECDHE-RSA-AES256-GCM-SHA384',
                                            is_sas=True)

  def generate_SSS_15_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_15. """
    # Create the actual config for SAS cert/key path

    config = {
        'sasCert': self.getCertFilename("sas_inapplicable.cert"),
        'sasKey': self.getCertFilename("sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_15_default_config)
  def test_WINNF_FT_S_SSS_15(self, config_filename):
    """Certificate with inapplicable fields presented during Full Activity Dump 
    """
    config = loadConfig(config_filename)
    
    # Reset the SAS UUT 
    self.SasReset()

    # Notify SAS UUT about peer SAS
    certificate_hash = getCertificateFingerprint(config['sasCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,\
                                     'url': SAS_TEST_HARNESS_URL })
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, ['AES128-GCM-SHA256'], config['sasCert'], config['sasKey'])
    trigger_succeed = False
    # Initiate Full Activity Dump
    try:
       self.TriggerFullActivityDumpAndWaitUntilComplete(config['sasCert'], config['sasKey'])
       trigger_succeed = True
    except HTTPError as e:
       # Check if HTTP status is 403
       self.assertEqual(e.error_code, 403)
    self.assertFalse(trigger_succeed, "Full Activity Dump is expected to fail")

  def generate_SSS_16_default_config(self, filename):
    """Generate the WinnForum configuration for SSS_16."""
    # Create the configuration for SAS cert/key path.

    config = {
        'sasCert': self.getCertFilename("sas_cert_from_revoked_ca.cert"),
        'sasKey': self.getCertFilename("sas_cert_from_revoked_ca.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_16_default_config)
  def test_WINNF_FT_S_SSS_16(self, config_filename):
    """Certificate signed by a revoked CA presented by SAS Test Harness.

    Checks that SAS UUT response with fatal alert message.
    """
    # Read the configuration
    config = loadConfig(config_filename)

    # Tls handshake fails since CA is revoked
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            is_sas=True)

    logging.info("TLS handshake failed as the CA certificate has been revoked")

  def generate_SSS_17_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_17"""
    # Create the actual config for SAS cert/key path

    config = {
        'sasCert': self.getCertFilename("sas.cert"),
        'sasKey': self.getCertFilename("sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_17_default_config)
  def test_WINNF_FT_S_SSS_17(self, config_filename):
    """Unknown SAS attempts to establish a TLS session.
    """
    config = loadConfig(config_filename)

    # Reset the SAS UUT
    self.SasReset()

    # Attempt TLS handshake without injecting peer SAS info and verify it fails
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['sasCert'],
                                            client_key=config['sasKey'],
                                            is_sas=True)

  def generate_SSS_18_default_config(self, filename):
    """ Generates the WinnForum configuration for SSS.18 """
    # Create the actual config for SAS cert/key path
    
    valid_cert_key_pair = {'cert' :self.getCertFilename("sas.cert"),
                           'key' :self.getCertFilename("sas.key")}
    invalid_cert_key_pair = {'cert' :self.getCertFilename("sas_expired.cert"),
                             'key' :self.getCertFilename("sas_expired.key")}

    config = {
        'validCertKeyPair': valid_cert_key_pair,
        'invalidCertKeyPair': invalid_cert_key_pair
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_18_default_config)
  def test_WINNF_FT_S_SSS_18(self, config_filename):
    """Security requirement for Full Activity Dump message Request
    """
    config = loadConfig(config_filename)

    # Reset the SAS UUT
    self.SasReset()

    # Notify SAS UUT about peer SAS
    certificate_hash = getCertificateFingerprint(config['validCertKeyPair']['cert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,\
                                     'url': SAS_TEST_HARNESS_URL })
    # Load a Device
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Load grant request
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted([device_a], [grant_a])

    # Initiate Full Activity Dump with valid cert, key pair
    fadResponse =  self.TriggerFullActivityDumpAndWaitUntilComplete(config['validCertKeyPair']['cert'], \
                                                                    config['validCertKeyPair']['key'])

    self.assertContainsRequiredFields("FullActivityDump.schema.json", fadResponse)
    url = fadResponse['files'][0]['url']

    # Attempting FAD record download with different invalid cert,key pair
    try:
      self.assertTlsHandshakeFailure(client_cert=config['invalidCertKeyPair']['cert'],
                                     client_key=config['invalidCertKeyPair']['key'])
    except AssertionError as e:
      try:
        self._sas.DownloadFile(url,config['invalidCertKeyPair']['cert'], \
                                                config['invalidCertKeyPair']['key'])
      except HTTPError as e:
        self.assertEqual(e.error_code, 403)
      else:
        self.fail("FAD record file download should have failed")
