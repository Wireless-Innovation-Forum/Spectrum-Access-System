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
import security_testcase
import time
from OpenSSL import SSL
from util import winnforum_testcase, configurable_testcase,\
  writeConfig, loadConfig


class SasCbsdSecurityTestcase(security_testcase.SecurityTestCase):
  # Tests changing the SAS UUT state must explicitly call the SasReset().

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_1(self):
    """New registration with TLS_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy cipher security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doCbsdTestCipher('AES128-GCM-SHA256',
                          self.getCertFilename('device.cert'),
                          self.getCertFilename('device.key'))

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_2(self):
    """New registration with TLS_RSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doCbsdTestCipher('AES256-GCM-SHA384',
                          self.getCertFilename('device.cert'),
                          self.getCertFilename('device.key'))

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_3(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a CBSD registration with this configuration succeed.
    Note that the test require a SAS UUT
    """
    self.doCbsdTestCipher('ECDHE-ECDSA-AES128-GCM-SHA256',
                          self.getCertFilename('device.cert'),
                          self.getCertFilename('device.key'))

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_4(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doCbsdTestCipher('ECDHE-ECDSA-AES256-GCM-SHA384',
                          self.getCertFilename('device.cert'),
                          self.getCertFilename('device.key'))

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_5(self):
    """New registration with TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a CBSD registration with this configuration succeed.
    """
    self.doCbsdTestCipher('ECDHE-RSA-AES128-GCM-SHA256',
                          self.getCertFilename('device.cert'),
                          self.getCertFilename('device.key'))

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
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['clientCert'],
                                            client_key=config['clientKey'])

  def generate_SCS_7_default_config(self, filename):
    """Generates the WinnForum configuration for SCS_7"""
    # Create the actual config for client cert/key path

    config = {
      'clientCert': self.getCertFilename("device_corrupted.cert"),
      'clientKey': self.getCertFilename("device_corrupted.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_7_default_config)
  def test_WINNF_FT_S_SCS_7(self,config_filename):
    """Corrupted certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['clientCert'],
                                            client_key=config['clientKey'])

  def generate_SCS_8_default_config(self, filename):
    """Generates the WinnForum configuration for SCS_8"""
    # Create the actual config for client cert/key path

    config = {
      'clientCert': self.getCertFilename("device_self_signed.cert"),
      'clientKey': self.getCertFilename("device.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_8_default_config)
  def test_WINNF_FT_S_SCS_8(self,config_filename):
    """Self-signed certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['clientCert'],
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
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['clientCert'],
                                            client_key=config['clientKey'])

  def generate_SCS_10_default_config(self, filename):
    """Generates the WinnForum configuration for SCS_10. """
    # Create the actual config for client cert/key path

    config = {
      'clientCert': self.getCertFilename("device_wrong_type.cert"),
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

  def generate_SCS_11_default_config(self, filename):
    """Generate the WinnForum configuration for SCS_11."""
    # Create the configuration for blacklisted client cert/key path

    config = {
        'clientCert': self.getCertFilename("device_blacklisted.cert"),
        'clientKey': self.getCertFilename("device_blacklisted.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_11_default_config)
  def test_WINNF_FT_S_SCS_11(self, config_filename):
    """Blacklisted certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    # Read the configuration
    config = loadConfig(config_filename)

    # Tls handshake fails or http 403 response
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['clientCert'],
                                            client_key=config['clientKey'])
    logging.info("TLS handshake failed as the client certificate has blacklisted")


  def generate_SCS_12_default_config(self, filename):
    """Generates the WinnForum configuration for SCS.12"""
    # Create the actual config for client cert/key path
    
    config = { 
        'clientCert': self.getCertFilename("device_expired.cert"),
        'clientKey': self.getCertFilename("device_expired.key")
    }
    writeConfig(filename, config)
  
  @configurable_testcase(generate_SCS_12_default_config)
  def test_WINNF_FT_S_SCS_12(self,config_filename):
    """Expired certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['clientCert'],
                                            client_key=config['clientKey'])

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_13(self):
    """ Disallowed TLS method attempted during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.assertTlsHandshakeFailureOrHttp403(ssl_method=SSL.TLSv1_1_METHOD)

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_14(self):
    """Invalid ciphersuite presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.assertTlsHandshakeFailureOrHttp403(ciphers='ECDHE-RSA-AES256-GCM-SHA384')

  def generate_SCS_15_default_config(self, filename):
    """ Generates the WinnForum configuration for SCS.15 """
    # Create the actual config for client cert/key path
    
    config = {
        'clientCert': self.getCertFilename("device_inapplicable.cert"),
        'clientKey': self.getCertFilename("device.key")
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

  def generate_SCS_16_default_config(self, filename):
    """Generate the WinnForum configuration for SCS_16."""
    # Create the configuration for client cert/key path.

    config = {
        'clientCert': self.getCertFilename("device_cert_from_revoked_ca.cert"),
        'clientKey': self.getCertFilename("device_cert_from_revoked_ca.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SCS_16_default_config)
  def test_WINNF_FT_S_SCS_16(self, config_filename):
    """Certificate signed by a revoked CA presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    # Read the configuration
    config = loadConfig(config_filename)

    # Tls handshake fails since CA is revoked
    self.assertTlsHandshakeFailureOrHttp403(client_cert=config['clientCert'],
                                            client_key=config['clientKey'])
    logging.info("TLS handshake failed as the CA certificate has been revoked")

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_17(self):
    """Invalid certificate following an approved registration request.

    Checks that SAS UUT response with fatal alert message.
    """
    device_cert_name = "short_lived_client"
    cert_duration_minutes = 1  # in minutes

    # Create a short lived certificate signed by intermediate CBSD CA.
    self.createShortLivedCertificate("CBSD", device_cert_name, cert_duration_minutes)

    # Get the absolute path of the short lived certificate created.
    device_cert = self.getCertFilename(device_cert_name + ".cert")
    device_key = self.getCertFilename(device_cert_name + ".key")

    # Successful TLS Handshake
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, ['AES128-GCM-SHA256'],
                                   device_cert, device_key)
    logging.info("TLS Handshake Succeeded")

    # Load the device_a file
    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Register device and grant device with certs(short lived certificates) to SAS UUT.
    # Ensure the registration and grant requests are successful.
    # The CiphersOverload approach is used in to override the default certificates with
    # the certificates configured for this test case.
    with security_testcase.CiphersOverload(self._sas, self._sas._tls_config.ciphers,
                                           device_cert, device_key):
      self.assertRegistered([device_a])

    logging.info("CBSD device is in registered state")

    # Wait for the short lived certificate to expire.
    wait_timer = (cert_duration_minutes * 60) + 5
    logging.info("Waiting for %s secs so the certificate will become invalid", wait_timer)
    time.sleep(wait_timer)

    # Verify TLS handshake fails
    logging.info("CBSD attempts to re-establish TLS Handshake with SAS UUT")
    self.assertTlsHandshakeFailureOrHttp403(client_cert=device_cert, client_key=device_key)
    logging.info("TLS handshake failed as the client certificate is invalid")

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_18(self):
    """Invalid certificate following an approved grant request.

    Checks that SAS UUT response with fatal alert message.
    """
    device_cert_name = "short_lived_client"
    cert_duration_minutes = 1  # in minutes

    # Create a short lived certificate signed by intermediate CBSD CA.
    self.createShortLivedCertificate("CBSD", device_cert_name, cert_duration_minutes)

    # Get the absolute path of the short lived certificate created.
    device_cert = self.getCertFilename(device_cert_name + ".cert")
    device_key = self.getCertFilename(device_cert_name + ".key")

    # Successful TLS Handshake
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, ['AES128-GCM-SHA256'], device_cert,
                                   device_key)
    logging.info("TLS Handshake Succeeded")

    # Load the device_a file
    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Load the grant_0 file
    grant_0 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    # Register device and grant device with certs(short lived certificates) to SAS UUT.
    # Ensure the registration and grant requests are successful.
    # The CiphersOverload approach is used in to override the default certificates with
    # the certificates configured for this test case.
    with security_testcase.CiphersOverload(self._sas, self._sas._tls_config.ciphers,
                                           device_cert, device_key):
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted([device_a], [grant_0])

    logging.info("CBSD is in Granted State")

    # Wait for the short lived certificate to expire.
    wait_timer = (cert_duration_minutes * 60) + 5
    logging.info("Waiting for %s secs so the certificate will become invalid", wait_timer)
    time.sleep(wait_timer)

    # Verify TLS handshake fails.
    logging.info("CBSD attempts to re-establish TLS Handshake with SAS UUT")
    self.assertTlsHandshakeFailureOrHttp403(client_cert=device_cert, client_key=device_key)
    logging.info("TLS handshake failed as the client certificate is invalid")

  @winnforum_testcase
  def test_WINNF_FT_S_SCS_19(self):
    """Invalid certificate following an approved heartbeat request.

    Checks that SAS UUT response with fatal alert message.
    """
    device_cert_name = "short_lived_client"
    cert_duration_minutes = 1  # in minutes

    # Create a short lived certificate signed by intermediate CBSD CA.
    self.createShortLivedCertificate("CBSD", device_cert_name, cert_duration_minutes)

    # Get the absolute path of the short lived certificate created.
    device_cert = self.getCertFilename(device_cert_name + ".cert")
    device_key = self.getCertFilename(device_cert_name + ".key")

    # Successful TLS Handshake.
    self.assertTlsHandshakeSucceed(self._sas_admin._base_url, ['AES128-GCM-SHA256'],
                                   device_cert, device_key)
    logging.info("TLS Handshake Succeeded")

    # Load the device_a file.
    device_a = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Load the grant_0 file.
    grant_0 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    # Register device and grant device with certs(short lived certificates) to SAS UUT.
    # Ensure the registration and grant requests are successful.
    # The CiphersOverload approach is used in to override the default certificates with
    # the certificates configured for this test case.
    with security_testcase.CiphersOverload(self._sas, self._sas._tls_config.ciphers,
                                           device_cert, device_key):
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted([device_a], [grant_0])
      operation_states = ['GRANTED']

      # Send the Heartbeat request for the Grant of CBSD to SAS UUT.
      transmit_expire_time = self.assertHeartbeatsSuccessful(cbsd_ids, grant_ids, operation_states)

    logging.info("CBSD is in HeartBeat Successful State")

    # Wait for the short lived certificate to expire.
    wait_timer = (cert_duration_minutes * 60) + 5
    logging.info("Waiting for %s secs so the certificate will become invalid", wait_timer)
    time.sleep(wait_timer)

    # Verify TLS handshake fails.
    logging.info("CBSD attempts to re-establish TLS Handshake with SAS UUT")
    self.assertTlsHandshakeFailureOrHttp403(client_cert=device_cert, client_key=device_key)
    logging.info("TLS handshake failed as the client certificate is invalid")
