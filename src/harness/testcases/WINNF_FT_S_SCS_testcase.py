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
import logging
import os
import re
import security_testcase
import socket
import urlparse
from binascii import a2b_base64
from cryptography.hazmat.primitives import serialization
from Crypto.Util.asn1 import DerSequence
from OpenSSL import crypto,SSL
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

  def generate_SCS_6_default_config(self, filename):
    """Generates the WinnForum configuration for SCS_6"""
    # Create the actual config for client cert/key path

    config = {
      'clientCert': self.getCertFilename("unrecognized_device.cert"),
      'clientKey': self.getCertFilename("unrecognized_device.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_6_default_config)
  def test_WINNF_FT_S_SCS_6(self, config_filename):
    """Unrecognized root of trust certificate presented during registration.

    Checks that SAS UUT response with fatal alert with unknown_ca.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['clientCert'],
                                   client_key=config['clientKey'])

  def generate_SCS_7_default_config(self, filename):
    """Generates the WinnForum configuration for SCS_7"""
    # Create the actual config for client cert/key path

    config = {
      'clientCert': self.getCertFilename("corrupted_client.cert"),
      'clientKey': self.getCertFilename("corrupted_client.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_7_default_config)
  def test_WINNF_FT_S_SCS_7(self,config_filename):
    """Corrupted certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['clientCert'],
                                   client_key=config['clientKey'])

  def generate_SCS_8_default_config(self, filename):
    """Generates the WinnForum configuration for SCS_8"""
    # Create the actual config for client cert/key path

    config = {
      'clientCert': self.getCertFilename("self_signed_client.cert"),
      'clientKey': self.getCertFilename("client.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_8_default_config)
  def test_WINNF_FT_S_SCS_8(self,config_filename):
    """Self-signed certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['clientCert'],
                                   client_key=config['clientKey'])

  def generate_SCS_9_default_config(self, filename):
    """Generates the WinnForum configuration for SCS_9"""
    # Create the actual config for client cert/key path

    config = {
      'clientCert': self.getCertFilename("non_cbrs_signed_device.cert"),
      'clientKey': self.getCertFilename("non_cbrs_signed_device.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_9_default_config)
  def test_WINNF_FT_S_SCS_9(self,config_filename):
    """Non-CBRS trust root signed certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['clientCert'],
                                   client_key=config['clientKey'])

  def generate_SCS_10_default_config(self, filename):
    """Generates the WinnForum configuration for SCS_10. """
    # Create the actual config for client cert/key path

    config = {
      'clientCert': self.getCertFilename("wrong_type_client.cert"),
      'clientKey': self.getCertFilename("server.key")

    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_10_default_config)
  def test_WINNF_FT_S_SCS_10(self,config_filename):
    """Certificate of wrong type presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    try:
      self.assertTlsHandshakeFailure(client_cert=config['clientCert'],
                                     client_key=config['clientKey'])
    except AssertionError as e:
      self.SasReset()
      # Load Devices
      device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
      # Register the devices
      devices = [device_a]
      request = {'registrationRequest': devices}
      response = self._sas.Registration(request, ssl_cert=config['clientCert'],
                                        ssl_key=config['clientKey'])['registrationResponse']
      # Check Registration Response
      self.assertEqual(response[0]['response']['responseCode'], 104)

  def generate_SCS_12_default_config(self, filename):
    """Generates the WinnForum configuration for SCS.12"""
    # Create the actual config for client cert/key path
    
    config = { 
        'clientCert': self.getCertFilename("client_expired.cert"),
        'clientKey': self.getCertFilename("client_expired.key")
    }
    writeConfig(filename, config)
  
  @configurable_testcase(generate_SCS_12_default_config)
  def test_WINNF_FT_S_SCS_12(self,config_filename):
    """Expired certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['clientCert'],
                                   client_key=config['clientKey'])

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
    config = loadConfig(config_filename)
    
    # Load the keys/certs and check that TLS handshake is valid
    device_a_cert = config['clientCert']
    device_a_key = config['clientKey']
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, ['AES128-GCM-SHA256'], device_a_cert, device_a_key)
   
    # Load device and inject fccId and userId
    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self.SasReset() 
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    
    # Send registration Request with certs(inapplicable fields) to SAS UUT 
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request,ssl_cert=device_a_cert,ssl_key=device_a_key)['registrationResponse'][0]

    # Check registration response
    self.assertEqual(response['response']['responseCode'],104)

  def generate_SCS_20_default_config(self,filename):
    """Generates the WinnForum configuration for SCS.20."""
    config = {
      'Issuer': {
          'countryName':'US',
          'stateOrProvinceName': 'District of Columbia',
          'localityName': 'Washington',
          'organizationName': 'Wireless Innovation Forum',
          'organizationalUnitName':'www.wirelessinnovation.org',
          'commonName':'WInnForum RSA SAS CA-1'
      },
      'Subject': {
          'countryName':'US',
          'stateOrProvinceName': 'District of Columbia',
          'localityName': 'Washington',
          'organizationName': 'Wireless Innovation Forum',
          'organizationalUnitName':'www.wirelessinnovation.org',
          'commonName':'localhost'
      },
      'clientCert':'client.cert',
      'clientKey':'client.key'
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_20_default_config)
  def test_WINNF_FT_S_SCS_20(self,config_filename):
    """
       SAS Certificate Validation
       This test case verifies fields of the server certificate based on the
       criteria provided in the test spec for WINNF.FT.S.SCS.20
    """
    config = loadConfig(config_filename)

    clientCert = self.getCertFilename(config['clientCert'])
    clientKey = self.getCertFilename(config['clientKey'])

    self.assertTlsHandshakeSucceedAndVerifyCertificate(self._sas_admin._base_url,
                                   ['AES128-GCM-SHA256'], clientCert,
                                                       clientKey,config)

  def assertTlsHandshakeSucceedAndVerifyCertificate(self, base_url, ciphers,
                                                    client_cert, client_key, config):
    """Checks that the TLS handshake succeed with the given parameters and
       verifies the leaf certificate.

    Attempts to establish a TLS session with the given |base_url|, using the
    given |ciphers| list and the given certificate key pair.
    After receiving the server certificate chain ,This function validates the leaf certificate
    parameters of the certificate chain.
    """
    url = urlparse.urlparse('https://' + base_url)
    client = socket.socket()
    client.connect((url.hostname, url.port or 443))
    logging.debug("OPENSSL version: %s" % SSL.SSLeay_version(SSL.SSLEAY_VERSION))
    logging.debug('TLS handshake: connecting to: %s:%d', url.hostname,
                  url.port or 443)
    logging.debug('TLS handshake: ciphers=%s', ':'.join(ciphers))
    logging.debug('TLS handshake: privatekey_file=%s', client_key)
    logging.debug('TLS handshake: certificate_file=%s', client_cert)
    logging.debug('TLS handshake: certificate_chain_file=%s',
                  self._sas._tls_config.ca_cert)

    ctx = SSL.Context(SSL.TLSv1_2_METHOD)
    ctx.set_cipher_list(':'.join(ciphers))
    ctx.use_certificate_file(client_cert)
    ctx.use_privatekey_file(client_key)
    ctx.load_verify_locations(self._sas._tls_config.ca_cert)

    client_ssl_informations = []
    def _InfoCb(conn, where, ok):
      client_ssl_informations.append(conn.get_state_string())
      logging.debug('TLS handshake info: %d|%d %s', where, ok, conn.get_state_string())
      return ok
    ctx.set_info_callback(_InfoCb)

    self.is_leaf_certificate_verified = False

    def validateSeverCertificateCallback(conn, cert, error_num, error_depth, ok):
      """
         This function validates the leaf certificate of a server based on the conditions
         mentioned in  WINNF.FT.S.SCS.20 test case
      """
      # Check the basic constraint which is CA:FALSE to access leaf certificate for validation
      if ("CA:FALSE" in str(cert.get_extension(2))):
          logging.info('Server Certificate Validation started')

          # Checks Issuer fileds
          logging.info('Common name field of Issuer=%s', cert.get_issuer().commonName)
          self.assertEqual(cert.get_issuer().commonName, config["Issuer"]["commonName"],
                           "Common name field of Issuer does not match")

          logging.info('countryName field of Issuer=%s', cert.get_issuer().countryName)
          self.assertEqual(cert.get_issuer().countryName, config["Issuer"]["countryName"],
                           "countryName field of Issuer does not match")

          logging.info('stateOrProvinceName field of Issuer=%s', cert.get_issuer().stateOrProvinceName)
          self.assertEqual(cert.get_issuer().stateOrProvinceName,
                           config["Issuer"]["stateOrProvinceName"],
                           "stateOrProvinceName field of Issuer does not match")

          logging.info('localityName field of Issuer=%s', cert.get_issuer().localityName)
          self.assertEqual(cert.get_issuer().localityName,config["Issuer"]["localityName"],
                           "localityName field of Issuer does not match")

          logging.info('organizationName field of Issuer=%s', cert.get_issuer().organizationName)
          self.assertEqual(cert.get_issuer().organizationName, config["Issuer"]["organizationName"],
                           "organizationName field of Issuer does not match")

          logging.info('organizationalUnitName field of Issuer=%s', cert.get_issuer().organizationalUnitName)
          self.assertEqual(cert.get_issuer().organizationalUnitName,
                           config["Issuer"]["organizationalUnitName"],
                           "organizationalUnitName field of Issuer does not match")

          # Checks the subject fields
          logging.info('commonName field of Subject=%s', cert.get_subject().commonName)
          self.assertEqual(cert.get_subject().commonName,
                             config["Subject"]["commonName"],
                             "Common name field of Subject does not match")

          logging.info('countryName field of Subject=%s', cert.get_subject().countryName)
          self.assertEqual(cert.get_subject().countryName,
                             config["Subject"]["countryName"],
                             "countryName field of Subject does not match")

          logging.info('stateOrProvinceName field of Subject=%s', cert.get_subject().stateOrProvinceName)
          self.assertEqual(cert.get_subject().stateOrProvinceName,
                             config["Subject"]["stateOrProvinceName"],
                             "stateOrProvinceName field of Subject does not match")

          logging.info('localityName field of Subject=%s', cert.get_subject().localityName)
          self.assertEqual(cert.get_subject().localityName,
                             config["Subject"]["localityName"],
                             "localityName field of Subject does not match")

          logging.info('organizationName field of Subject=%s', cert.get_subject().organizationName)
          self.assertEqual(cert.get_subject().organizationName,
                             config["Subject"]["organizationName"],
                             "organizationName field of Subject does not match")

          logging.info('organizationalUnitName field of Subject=%s', cert.get_subject().organizationalUnitName)
          self.assertEqual(cert.get_subject().organizationalUnitName,
                             config["Subject"]["organizationalUnitName"],
                             "organizationalUnitName field of Subject does not match")

          # Version validation
          logging.info('certificate version=%d', cert.get_version())
          self.assertEqual(cert.get_version(), 2, "version != 2")

          # Serial number validation
          logging.info('serial number=%d', cert.get_serial_number())
          serial_number = cert.get_serial_number()
          self.assertGreater(serial_number, 0, "serial number not a positive integer")
          self.assertLessEqual(len(str(serial_number)), 20)

          # Check for algorithm ID
          logging.info('Algorith ID %d', cert.get_pubkey().type())
          self.assertIn(cert.get_pubkey().type(),[crypto.TYPE_RSA,crypto.TYPE_DSA],
                        "algorithm Id not RSA or DSA")

          #Date validity
          # This check for Not Before field is encoded as UTCTime if before
          # the year 2050, or GeneralizedTime for dates in 2050 or later
          # is internally addressed by pyopenssl v17.5.0 library within the get_notBefore method.
          # Hence if the this method does not return NoneType then this condition is satisfied.
          not_before = cert.get_notBefore()
          logging.info('not_before %s', not_before)
          self.assertIsNotNone(not_before, "not_before field validation failed")

          # This check for Not After field is encoded as UTCTime if before
          # the year 2050, or GeneralizedTime for dates in 2050 or later
          # is internally addressed by pyopenssl v17.5.0 library within the get_notAfter method.
          # Hence if the this method does not return NoneType then this condition is satisfied.
          not_after = cert.get_notAfter()
          logging.info('not_after %s', not_before)
          self.assertIsNotNone(not_after, "not_after field validation failed")

          # Subject public key Info validation
          pubkey = cert.get_pubkey()
          self.assertGreaterEqual(pubkey.bits(), 2048,
                                    "Public key should be greater or equal to 2048 bits")
          signature_algorithm = cert.get_signature_algorithm()
          signature_algorithm_list = ["sha256WithRSAEncryption",
                                        "sha384WithRSAEncryption",
                                        "sha512WithRSAEncryption",
                                        "ecdsa-with-Sha256",
                                        "ecdsa-with-Sha384",
                                        "ecdsa-with-Sha512"]
          self.assertIn(signature_algorithm, signature_algorithm_list,
                          "No matching signature algorithm found")
          logging.info('signature algorithm=%s', cert.get_signature_algorithm())

          # CA:FALSE check is already satisfied while choosing the leaf certificate

          #Subject: Common Name (CN) is already validated above

          extension_count = cert.get_extension_count()
          extension_index = 0
          basic_constraints_evaluated = False
          certificate_policies_evaluated  = False
          while (extension_index < extension_count):
            extension = cert.get_extension(extension_index)
            logging.info('Extracted extension %s',extension.__str__())
            if (extension.get_short_name() == "basicConstraints"):
                # Path length constraint is None
                self.assertNotIn("pathlen", extension.__str__(), "Path Length Constraint is present")
                basic_constraints_evaluated = True
            elif (extension.get_short_name() == "certificatePolicies"):
                # Check for ROLE SAS exist
                self.assertIn("1.3.6.1.4.1.46609.1.1.1", extension.__str__(),
                              "ROLE=SAS does not exist in Certificate Policies")
                # Check for FRN exist
                self.assertIn("1.3.6.1.4.1.46609.1.6", extension.__str__(),
                              "FRN does not exist in Certificate Policies")
                # The provided certificate does not contain the following custom SAS OIDs
                # ZONE does not exist
                self.assertNotIn("1.3.6.1.4.1.46609.1.2", extension.__str__(),
                                 "ZONE exist in Certificate Policies")

                # FREQUENCY does not exist
                self.assertNotIn("1.3.6.1.4.1.46609.1.3", extension.__str__(),
                                 "FREQUENCY exist in Certificate Policies")

                # FCCID does not exist
                self.assertNotIn("1.3.6.1.4.1.46609.1.4", extension.__str__(),
                                 "FCCID exist in Certificate Policies")

                # SERIAL does not exist
                self.assertNotIn("1.3.6.1.4.1.46609.1.5", extension.__str__(),
                                 "SERIAL exist in Certificate Policies")

                # CPIRID does not exist
                self.assertNotIn("1.3.6.1.4.1.46609.1.7", extension.__str__(),
                                 "CPIRID exist in Certificate Policies")
                certificate_policies_evaluated = True
            extension_index = extension_index+1

          # Check if the basic constraints is found and evaluated
          self.assertTrue(basic_constraints_evaluated,"basic constraints extension not found")

          # Check for valid CBRS root of trust is satisfied by the verification of handshake success

          # Check if the certificate policies is found and evaluated
          self.assertTrue(certificate_policies_evaluated, "certificate policies extension not found")

          logging.info("All fields in certificates are validated successfully")
          self.is_leaf_certificate_verified = True
      return ok
    ctx.set_verify(SSL.VERIFY_PEER, validateSeverCertificateCallback)

    client_ssl = SSL.Connection(ctx, client)
    client_ssl.set_connect_state()
    client_ssl.set_tlsext_host_name(url.hostname)

    try:
      client_ssl.do_handshake()
      logging.debug('TLS handshake: succeed')
    except SSL.Error as e:
      logging.exception('TLS handshake: failed:\n%s', '\n'.join(client_ssl_informations))
      raise AssertionError('TLS handshake: failure: %s' % e.message)
    finally:
      client_ssl.close()

    # Check if the leaf certificate validated
    self.assertTrue(self.is_leaf_certificate_verified, "leaf certificate not validated")
    self.assertEqual(client_ssl.get_cipher_list(), ciphers)
    self.assertEqual(client_ssl.get_protocol_version_name(), 'TLSv1.2')

    # tricky part: exact logged message depends of the version of openssl...
    cipher_check_regex = re.compile(r"change.cipher.spec", re.I)
    finished_check_regex = re.compile(r"negotiation finished|finish_client_handshake", re.I)
    def findIndexMatching(array, regex):
      for i, x in enumerate(array):
        if regex.search(x):
          return i
      return -1
    cipher_check_idx = findIndexMatching(client_ssl_informations, cipher_check_regex)
    finished_check_idx = findIndexMatching(client_ssl_informations, finished_check_regex)
    self.assertTrue(cipher_check_idx > 0)
    self.assertTrue(finished_check_idx > 0)
    self.assertTrue(finished_check_idx > cipher_check_idx)
