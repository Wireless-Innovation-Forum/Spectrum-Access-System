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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os

from reference_models.antenna import antenna
from reference_models.geo import utils
from reference_models.propagation import wf_itm
import sas
import sas_testcase
from util import configurable_testcase, writeConfig, loadConfig, json_load


class BorderProtectionTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_BPR_2_default_config(self, filename):
    """Generates the WinnForum configuration for BPR.2."""

    # CBSD 1: Category A CBSD within 56 km of the Canadian border with
    # omni-directional antenna.
    device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_1['installationParam']['latitude'] = 48.99781
    device_1['installationParam']['longitude'] = -100.959089
    device_1['installationParam']['antennaBeamwidth'] = 0
    device_1['installationParam']['height'] = 1.2
    # CBSD 2: Category B CBSD within 56 km of the Canadian border with
    # omni-directional antenna.
    device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_2['installationParam']['latitude'] = 42.273371
    device_2['installationParam']['longitude'] = -83.746700
    device_2['installationParam']['antennaBeamwidth'] = 0
    device_1['installationParam']['antennaGain'] = 90
    # CBSD 3: Category A CBSD located within 8 km of the Canadian border with
    # directive antenna
    device_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_3['installationParam']['latitude'] = 48.939190
    device_3['installationParam']['longitude'] = -122.475071
    device_3['installationParam']['antennaBeamwidth'] = 30
    # CBSD 4: Category B CBSD located within 8 km of the Canadian border with
    # directive antenna
    device_4 = json_load(
        os.path.join('testcases', 'testdata', 'device_d.json'))
    device_4['installationParam']['latitude'] = 48.964667
    device_4['installationParam']['longitude'] = -122.441425
    device_4['installationParam']['antennaBeamwidth'] = 60
    # CBSD 5: Category A CBSD located between 8 km and 56 km of the Canadian
    # border with directive antenna of which any part of the main beam looks
    # within 200-degree sector toward the closest point on the Canadian border.
    device_5 = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
    device_5['installationParam']['latitude'] = 48.806222
    device_5['installationParam']['longitude'] = -111.874259
    device_5['installationParam']['antennaAzimuth'] = 0
    # CBSD 6: Category B CBSD located between 8 km and 56 km of the Canadian
    # border with directive antenna of which any part of the main beam looks
    # within 200-degree sector toward the closest point on the Canadian border.
    device_6 = json_load(
        os.path.join('testcases', 'testdata', 'device_h.json'))
    device_6['installationParam']['latitude'] = 42.273371
    device_6['installationParam']['longitude'] = -83.746700
    device_6['installationParam']['antennaAzimuth'] = 0

    # device_1, device_3, device_5 are Category A.
    self.assertEqual(device_1['cbsdCategory'], 'A')
    self.assertEqual(device_3['cbsdCategory'], 'A')
    self.assertEqual(device_5['cbsdCategory'], 'A')

    # device_2, device_4, device_6 are Category B.
    self.assertEqual(device_2['cbsdCategory'], 'B')
    self.assertEqual(device_4['cbsdCategory'], 'B')
    self.assertEqual(device_6['cbsdCategory'], 'B')

    # Conditionals to pre-load
    conditionals_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }
    conditionals_4 = {
        'cbsdCategory': device_4['cbsdCategory'],
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'],
        'installationParam': device_4['installationParam'],
        'measCapability': device_4['measCapability']
    }
    conditionals_6 = {
        'cbsdCategory': device_6['cbsdCategory'],
        'fccId': device_6['fccId'],
        'cbsdSerialNumber': device_6['cbsdSerialNumber'],
        'airInterface': device_6['airInterface'],
        'installationParam': device_6['installationParam'],
        'measCapability': device_6['measCapability']
    }

    # Remove conditionals from registration.
    for device in [device_2, device_4, device_6]:
      del device['cbsdCategory']
      del device['airInterface']
      del device['installationParam']
      del device['measCapability']

    # Grant Requests
    grant_1 = {
        'operationParam': {
            'maxEirp': 19,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant_2 = {
        'operationParam': {
            'maxEirp': 37,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant_3 = {
        'operationParam': {
            'maxEirp': 19,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant_4 = {
        'operationParam': {
            'maxEirp': 37,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant_5 = {
        'operationParam': {
            'maxEirp': 19,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant_6 = {
        'operationParam': {
            'maxEirp': 37,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }

    # Create the actual config.
    conditionals = [conditionals_2, conditionals_4, conditionals_6]
    devices = [device_1, device_2, device_3, device_4, device_5, device_6]
    config = {
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
        'grantRequests': [grant_1, grant_2, grant_3, grant_4, grant_5, grant_6]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_BPR_2_default_config)
  def test_WINNF_FT_S_BPR_2(self, config_filename):
    """[Configurable] Grant Request from CBSDs within the Shared Zone adjacent
      the Canadian border.
    """
    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'registrationRequests': list,
            'conditionalRegistrationData': list,
            'grantRequests': list
        })
    self.assertEqual(
        len(config['registrationRequests']), len(config['grantRequests']))

    # Whitelist FCC ID and User ID.
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

    # Check registration response.
    self.assertEqual(len(responses), len(config['registrationRequests']))
    grant_request = []
    index_of_devices_with_success_registration_response = []
    for i, response in enumerate(responses):
      if response['response']['responseCode'] == 0:
        self.assertTrue('cbsdId' in response)
        index_of_devices_with_success_registration_response.append(i)
        config['grantRequests'][i]['cbsdId'] = response['cbsdId']
        grant_request.append(config['grantRequests'][i])
    del request, responses

    if not grant_request:
      return  # SAS passes immediately, since none of the registration requests
      # succeeded in this case.

    # For CBSDs successfully registered in Step 1, Send grant request
    request = {'grantRequest': grant_request}
    responses = self._sas.Grant(request)['grantResponse']
    # Check grant response
    self.assertEqual(len(responses), len(grant_request))
    self.assertEqual(
        len(responses),
        len(index_of_devices_with_success_registration_response))

    for i, index in enumerate(
        index_of_devices_with_success_registration_response):
      logging.info('Looking at Grant response number: %d', i)
      if (config['grantRequests'][i]['operationParam']
          ['operationFrequencyRange']['highFrequency'] <= 3650e6):
        logging.info(
            'Grant is not subject to Arrangement R because it does not overlap '
            'with 3650-3700 MHz.')
        continue

      if 'installationParam' in config['registrationRequests'][index]:
        cbsd_information = config['registrationRequests'][index]
      else:
        for conditional in config['conditionalRegistrationData']:
          if (config['registrationRequests'][index]['fccId'] ==
              conditional['fccId']) and (
                  config['registrationRequests'][index]['cbsdSerialNumber'] ==
                  conditional['cbsdSerialNumber']):
            cbsd_information = conditional
      cbsd_lat = cbsd_information['installationParam']['latitude']
      cbsd_lon = cbsd_information['installationParam']['longitude']
      cbsd_ant_azi = cbsd_information['installationParam']['antennaAzimuth']
      cbsd_ant_beamwidth = cbsd_information['installationParam'][
          'antennaBeamwidth']
      # Check if CBSD is in the Border Sharing Zone, Get the closest point.
      (is_in_sharing_zone, closest_point_lat,
       closest_point_lon) = utils.CheckCbsdInBorderSharingZone(
           cbsd_lat, cbsd_lon, cbsd_ant_azi, cbsd_ant_beamwidth)
      logging.info('CBSD is in Border Sharing Zone?: %s', is_in_sharing_zone)
      if not is_in_sharing_zone:
        continue  # CBSD not in the sharing zone; no PFD check is required.

      # Proceed with PFD calculation
      logging.info('Closest point in the border: Lat is %f', closest_point_lat)
      logging.info('Closest point in the border: Long is %f', closest_point_lon)
      # requested_eirp (p)
      p = config['grantRequests'][index]['operationParam']['maxEirp']
      # Calculate PL
      cbsd_height = cbsd_information['installationParam']['height']
      cbsd_height_type = cbsd_information['installationParam']['heightType']
      is_cbsd_indoor = cbsd_information['installationParam']['indoorDeployment']
      closest_point_height = 1.5  # According to the spec
      freq_mhz = 3625.  # Always in all SAS
      propagation = wf_itm.CalcItmPropagationLoss(
          cbsd_lat,
          cbsd_lon,
          cbsd_height,
          closest_point_lat,
          closest_point_lon,
          closest_point_height,
          reliability=0.5,
          cbsd_indoor=is_cbsd_indoor,
          freq_mhz=freq_mhz,
          is_height_cbsd_amsl=(cbsd_height_type == 'AMSL'))
      pl = propagation.db_loss
      logging.info('Propagation - db_loss: %f', propagation.db_loss)
      bearing = propagation.incidence_angles.hor_cbsd
      logging.info('Bearing: %f', propagation.incidence_angles.hor_cbsd)
      # Calculate effective antenna gain
      max_ant_gain = cbsd_information['installationParam']['antennaGain']
      ant_gain = antenna.GetStandardAntennaGains(
          bearing, cbsd_ant_azi, cbsd_ant_beamwidth,
          max_ant_gain)
      logging.info('Effective Antenna Gain: %f', ant_gain)
      # Calculate PFD where:
      # p = requested_eirp
      # effective_eirp = p - maxAntGain + antGain
      # PFD = effective_eirp - pl + 32.6
      pfd = p - max_ant_gain + ant_gain - pl + 32.6
      logging.info('Power Flex Density: %f dBm/m2/MHz', pfd)
      if pfd > -80:
        self.assertTrue(responses[i]['response']['responseCode'] == 400)
