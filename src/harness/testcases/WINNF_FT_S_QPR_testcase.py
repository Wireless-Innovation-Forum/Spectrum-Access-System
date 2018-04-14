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
import sas
import sas_testcase
from util import configurable_testcase, writeConfig, loadConfig


class QuietZoneProtectionTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_QPR_2_default_config(self, filename):
    """Generates the WinnForum configuration for QPR.2."""

    # Load device info
    # CBSD 1: Category A CBSD located within the boundary of the NRAO / NRRO
    # Quiet Zone.
    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_1['installationParam']['latitude'] = 39.244586
    device_1['installationParam']['longitude'] = -78.505269

    # CBSD 2: Category B CBSD located within the boundary of the NRAO / NRRO
    # Quiet Zone.
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_2['installationParam']['latitude'] = 39.247287
    device_2['installationParam']['longitude'] = -80.489236

    # device_1 is Category A.
    self.assertEqual(device_1['cbsdCategory'], 'A')

    # device_2 is Category B with conditionals pre-loaded.
    self.assertEqual(device_2['cbsdCategory'], 'B')
    conditionals_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }
    conditionals = [conditionals_2]
    del device_2['installationParam']
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['measCapability']

    # Create the actual config.
    devices = [device_1, device_2]
    config = {
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_QPR_2_default_config)
  def test_WINNF_FT_S_QPR_2(self, config_filename):
    """[Configurable] Rejecting Registration of CBSD inside the NRAO/NRRO
      Quiet Zone.
    """
    config = loadConfig(config_filename)

    # Whitelist FCC IDs and User IDs.
    for device in config['registrationRequests']:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # Pre-load conditional registration data.
    if config['conditionalRegistrationData']:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    # Register CBSDs.
    request = {'registrationRequest': config['registrationRequests']}
    responses = self._sas.Registration(request)['registrationResponse']

    # Check registration responses.
    self.assertEqual(len(responses), len(config['registrationRequests']))
    for i, response in enumerate(responses):
      response = responses[i]
      logging.debug('Looking at response number %d', i)
      self.assertNotEqual(response['response']['responseCode'], 0)
      self.assertFalse('cbsdId' in response)

  def generate_QPR_6_default_config(self, filename):
    """Generates the WinnForum configuration for QPR.6."""

    # Load device info
    # CBSD 1: Category A within 2.4 km of Waipahu, Hawaii FCC Field Office.
    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_1['installationParam']['latitude'] = 21.377719
    device_1['installationParam']['longitude'] = -157.973411

    # CBSD 2: Category B within 2.4 km of Allegan, Michigan FCC Field Office.
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_2['installationParam']['latitude'] = 42.586213
    device_2['installationParam']['longitude'] = -85.955594

    # device_1 is Category A.
    self.assertEqual(device_1['cbsdCategory'], 'A')

    # device_2 is Category B with conditionals pre-loaded.
    self.assertEqual(device_2['cbsdCategory'], 'B')
    conditionals_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }
    conditionals = [conditionals_2]
    del device_2['installationParam']
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['measCapability']

    # Create the actual config.
    devices = [device_1, device_2]
    config = {
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_QPR_6_default_config)
  def test_WINNF_FT_S_QPR_6(self, config_filename):
    """[Configurable] Rejecting Registration of CBSDs inside the FCC Protected
      Field Offices Quiet Zone.
    """
    config = loadConfig(config_filename)

    # Whitelist FCC IDs and User IDs.
    for device in config['registrationRequests']:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # Pre-load conditional registration data.
    if config['conditionalRegistrationData']:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    # Register CBSDs.
    request = {'registrationRequest': config['registrationRequests']}
    responses = self._sas.Registration(request)['registrationResponse']

    # Check registration responses.
    self.assertEqual(len(responses), len(config['registrationRequests']))
    for i, response in enumerate(responses):
      response = responses[i]
      logging.debug('Looking at response number %d', i)
      self.assertNotEqual(response['response']['responseCode'], 0)
      self.assertFalse('cbsdId' in response)
