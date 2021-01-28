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
import numpy as np

import sas
import sas_testcase
from util import configurable_testcase, writeConfig, loadConfig, json_load
from reference_models.antenna import antenna
from reference_models.geo import vincenty
from reference_models.geo import zones
from reference_models.propagation import wf_itm


class QuietZoneProtectionTestcase(sas_testcase.SasTestCase):

  @classmethod
  def setUpClass(cls):
    super(QuietZoneProtectionTestcase, cls).setUpClass()
    cls.fcc_offices = zones.GetFccOfficeLocations()

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
    device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_1['installationParam']['latitude'] = 39.244586
    device_1['installationParam']['longitude'] = -78.505269

    # CBSD 2: Category B CBSD located within the boundary of the NRAO / NRRO
    # Quiet Zone.
    device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
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
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'registrationRequests': list,
            'conditionalRegistrationData': list
        })

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

  def generate_QPR_5_default_config(self, filename):
    """Generates the WinnForum configuration for QPR.5."""

    # CBSD 1: Category A CBSD within 3.8 km of the Table Mountain QZ
    device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_1['installationParam']['latitude'] = 40.121452
    device_1['installationParam']['longitude'] = -105.23381

    # CBSD 2: Category B CBSD within 38 km of the Table Mountain QZ
    device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_2['installationParam']['latitude'] = 40.271668
    device_2['installationParam']['longitude'] = -105.101395

    # CBSD 3: Category B CBSD within 54 km of the Table Mountain QZ
    device_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_d.json'))
    device_3['installationParam']['latitude'] = 40.175726
    device_3['installationParam']['longitude'] = -104.654388

    # CBSD 4: Category B CBSD within 64 km of the Table Mountain QZ
    device_4 = json_load(
        os.path.join('testcases', 'testdata', 'device_h.json'))
    device_4['installationParam']['latitude'] = 40.074919
    device_4['installationParam']['longitude'] = -104.523926

    # CBSD 5: Category B CBSD located within 80 km of the Table Mountain QZ
    device_5 = json_load(
        os.path.join('testcases', 'testdata', 'device_j.json'))
    device_5['installationParam']['latitude'] = 40.525283
    device_5['installationParam']['longitude'] = -104.547272

    # device_1 is Category A.
    self.assertEqual(device_1['cbsdCategory'], 'A')

    # device_2, device_3, device_4 and device_5 are Category B.
    self.assertEqual(device_2['cbsdCategory'], 'B')
    self.assertEqual(device_3['cbsdCategory'], 'B')
    self.assertEqual(device_4['cbsdCategory'], 'B')
    self.assertEqual(device_5['cbsdCategory'], 'B')

    # Conditionals to pre-load
    conditionals_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }
    conditionals_3 = {
        'cbsdCategory': device_3['cbsdCategory'],
        'fccId': device_3['fccId'],
        'cbsdSerialNumber': device_3['cbsdSerialNumber'],
        'airInterface': device_3['airInterface'],
        'installationParam': device_3['installationParam'],
        'measCapability': device_3['measCapability']
    }
    conditionals_4 = {
        'cbsdCategory': device_4['cbsdCategory'],
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'],
        'installationParam': device_4['installationParam'],
        'measCapability': device_4['measCapability']
    }
    conditionals_5 = {
        'cbsdCategory': device_5['cbsdCategory'],
        'fccId': device_5['fccId'],
        'cbsdSerialNumber': device_5['cbsdSerialNumber'],
        'airInterface': device_5['airInterface'],
        'installationParam': device_5['installationParam'],
        'measCapability': device_5['measCapability']
    }

    # Remove conditionals from registration.
    for device in [device_2, device_3, device_4, device_5]:
      del device['cbsdCategory']
      del device['airInterface']
      del device['installationParam']
      del device['measCapability']

    # Grant Requests - N1
    grant1N1 = {
        'operationParam': {
            'maxEirp': 19,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant2N1 = {
        'operationParam': {
            'maxEirp': 37,
            'operationFrequencyRange': {
                'lowFrequency': 3655000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant3N1 = {
        'operationParam': {
            'maxEirp': 35,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant4N1 = {
        'operationParam': {
            'maxEirp': 33,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant5N1 = {
        'operationParam': {
            'maxEirp': 30,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3670000000
            }
        }
    }
    # Grant Requests - N2
    grant1N2 = {
        'operationParam': {
            'maxEirp': 19,
            'operationFrequencyRange': {
                'lowFrequency': 3660000000,
                'highFrequency': 3670000000
            }
        }
    }
    grant2N2 = {
        'operationParam': {
            'maxEirp': 37,
            'operationFrequencyRange': {
                'lowFrequency': 3660000000,
                'highFrequency': 3665000000
            }
        }
    }
    grant3N2 = {
        'operationParam': {
            'maxEirp': 36,
            'operationFrequencyRange': {
                'lowFrequency': 3660000000,
                'highFrequency': 3670000000
            }
        }
    }
    grant4N2 = {
        'operationParam': {
            'maxEirp': 37,
            'operationFrequencyRange': {
                'lowFrequency': 3660000000,
                'highFrequency': 3680000000
            }
        }
    }
    grant5N2 = {
        'operationParam': {
            'maxEirp': 35,
            'operationFrequencyRange': {
                'lowFrequency': 3670000000,
                'highFrequency': 3690000000
            }
        }
    }
    # Create the actual config.
    config = {
        'registrationRequests': [
            device_1, device_2, device_3, device_4, device_5
        ],
        'conditionalRegistrationData': [
            conditionals_2, conditionals_3, conditionals_4, conditionals_5
        ],
        'grantRequestsN1': [grant1N1, grant2N1, grant3N1, grant4N1, grant5N1],
        'grantRequestsN2': [grant1N2, grant2N2, grant3N2, grant4N2, grant5N2]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_QPR_5_default_config)
  def test_WINNF_FT_S_QPR_5(self, config_filename):
    """[Configurable] Unsuccessful Grant Request from CBSDs within Coordination
    Area around Table Mountain Quiet Zone (QZ) with Multiple Grants.
    """
    config = loadConfig(config_filename)
    self.assertValidConfig(
        config, {
            'registrationRequests': list,
            'conditionalRegistrationData': list,
            'grantRequestsN1': list,
            'grantRequestsN2': list
        })
    self.assertEqual(
        len(config['registrationRequests']), len(config['grantRequestsN1']))
    self.assertEqual(
        len(config['grantRequestsN1']), len(config['grantRequestsN2']))

    # Whitelist FCC ID and User ID.
    for device in config['registrationRequests']:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # Pre-load conditional registration data.
    if config['conditionalRegistrationData']:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    # Step 1: Register CBSDs.
    request = {'registrationRequest': config['registrationRequests']}
    responses = self._sas.Registration(request)['registrationResponse']

    # Check registration response.
    self.assertEqual(len(responses), len(config['registrationRequests']))
    grant_request_n1 = []
    grant_request_n2 = []
    successful_reg_requests = []
    for i, response in enumerate(responses):
      if response['response']['responseCode'] == 0:
        self.assertTrue('cbsdId' in response)
        successful_reg_requests.append(config['registrationRequests'][i])
        config['grantRequestsN1'][i]['cbsdId'] = response['cbsdId']
        grant_request_n1.append(config['grantRequestsN1'][i])
        config['grantRequestsN2'][i]['cbsdId'] = response['cbsdId']
        grant_request_n2.append(config['grantRequestsN2'][i])
    del request, responses

    if not successful_reg_requests:
      return  # SAS passes immediately, since none of the registration requests
      # succeeded in this case.

    # Step 2: For CBSDs successfully registered in Step 1, Send grant request 1
    request1 = {'grantRequest': grant_request_n1}
    grant_responses1 = self._sas.Grant(request1)['grantResponse']
    # Check grant response 1
    self.assertEqual(len(grant_responses1), len(grant_request_n1))

    # Step 3: For CBSDs successfully registered in Step 1, Send grant request 2
    request2 = {'grantRequest': grant_request_n2}
    grant_responses2 = self._sas.Grant(request2)['grantResponse']
    # Check grant response 2
    self.assertEqual(len(grant_responses2), len(grant_request_n2))

    for i, device in enumerate(successful_reg_requests):
      if 'installationParam' in device:
        cbsd_information = device
      else:
        for conditional in config['conditionalRegistrationData']:
          if (device['fccId'] == conditional['fccId']) and (
              device['cbsdSerialNumber'] == conditional['cbsdSerialNumber']):
            cbsd_information = conditional
      logging.info(
          'Looking at device with FccID: %s / CbsdSerialNumber: %s',
          cbsd_information['fccId'], cbsd_information['cbsdSerialNumber'])
      grant_response1 = grant_responses1[i]
      grant_response2 = grant_responses2[i]
      if not (grant_response1['response']['responseCode'] == 0 or
              grant_response2['response']['responseCode'] == 0):
        logging.info('Both grant requests were rejected for this device.')
        continue  # Skip further calculation for this device.

      # Calculate PL
      logging.info(
          'Calculating PL for device with FccID: %s / CbsdSerialNumber: %s',
          cbsd_information['fccId'], cbsd_information['cbsdSerialNumber'])
      cbsd_lat = cbsd_information['installationParam']['latitude']
      cbsd_lon = cbsd_information['installationParam']['longitude']
      cbsd_ant_azi = cbsd_information['installationParam']['antennaAzimuth']
      cbsd_ant_beamwidth = cbsd_information['installationParam'][
          'antennaBeamwidth']
      cbsd_height = cbsd_information['installationParam']['height']
      cbsd_height_type = cbsd_information['installationParam']['heightType']
      is_cbsd_indoor = cbsd_information['installationParam']['indoorDeployment']
      freq_mhz = 3625.  # Always in all SAS
      table_mountain_quiet_zone_lat = 40.130660
      table_mountain_quiet_zone_long = -105.244596
      table_mountain_quiet_zone_height = 9  # 9 m: According to the spec
      propagation = wf_itm.CalcItmPropagationLoss(
          cbsd_lat,
          cbsd_lon,
          cbsd_height,
          table_mountain_quiet_zone_lat,
          table_mountain_quiet_zone_long,
          table_mountain_quiet_zone_height,
          cbsd_indoor=is_cbsd_indoor,
          reliability=0.5,
          freq_mhz=freq_mhz,
          is_height_cbsd_amsl=(cbsd_height_type == 'AMSL'))
      pl = propagation.db_loss
      logging.info('Propagation:db_loss: %f', pl)
      bearing = propagation.incidence_angles.hor_cbsd
      logging.info('Bearing: %f', bearing)
      # Calculate effective antenna gain
      max_ant_gain_dbi = cbsd_information['installationParam']['antennaGain']
      ant_gain_dbi = antenna.GetStandardAntennaGains(
          bearing, cbsd_ant_azi, cbsd_ant_beamwidth,
          max_ant_gain_dbi)
      logging.info('Effective Antenna Gain: %f', ant_gain_dbi)

      # Gather values required for calculating Total Interference
      grant1_eirp = 0
      if grant_response1['response']['responseCode'] == 0:
        p1 = grant_request_n1[i]['operationParam']['maxEirp']
        logging.info('Grant 1 Max Eirp: %f dBm/MHz', p1)
        bw1 = (grant_request_n1[i]['operationParam']
               ['operationFrequencyRange']['highFrequency'] -
               grant_request_n1[i]['operationParam']
               ['operationFrequencyRange']['lowFrequency']) / 1.e6
        logging.info('Grant 1 Bandwidth: %f', bw1)
        grant1_eirp = (10**(p1/10.0)) * bw1
        logging.info('Grant 1 EIRP is %f', grant1_eirp)

      grant2_eirp = 0
      if grant_response2['response']['responseCode'] == 0:
        p2 = grant_request_n2[i]['operationParam']['maxEirp']
        logging.info('Grant 2 Max Eirp: %f dBm/MHz', p2)
        bw2 = (grant_request_n2[i]['operationParam']
               ['operationFrequencyRange']['highFrequency'] -
               grant_request_n2[i]['operationParam']
               ['operationFrequencyRange']['lowFrequency']) / 1.e6
        logging.info('Grant 2 Bandwidth: %f', bw2)
        grant2_eirp = (10**(p2/10.0)) * bw2
        logging.info('Grant 2 EIRP is %f', grant2_eirp)

      # Step 4: Calculate Total Interference
      total_interference_dbm = ant_gain_dbi - max_ant_gain_dbi + (
          10 * np.log10(grant1_eirp + grant2_eirp)) - pl
      logging.info('Total Interference is %f dBm', total_interference_dbm)

      # CHECK: Total Interference from all approved grants is <= -88.4 dBm
      self.assertLessEqual(total_interference_dbm, -88.4)

  def generate_QPR_6_default_config(self, filename):
    """Generates the WinnForum configuration for QPR.6."""

    # Load device info
    # CBSD 1: Category A within 2.4 km of Waipahu, Hawaii FCC Field Office.
    device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_1['installationParam']['latitude'] = 21.377719
    device_1['installationParam']['longitude'] = -157.973411

    # CBSD 2: Category B within 2.4 km of Allegan, Michigan FCC Field Office.
    device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
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
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'registrationRequests': list,
            'conditionalRegistrationData': list
        })

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

  def generate_QPR_7_default_config(self, filename):
    """Generates the WinnForum configuration for QPR.7."""

    # Load device info
    # Cat B - between 2.4 km - 4.8 km of Waipahu, Hawaii Field Office.
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_b['installationParam']['latitude'] = 21.397934
    device_b['installationParam']['longitude'] = -158.034459

    # device_b is Category B with conditionals pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam'],
        'measCapability': device_b['measCapability']
    }
    del device_b['installationParam']
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['measCapability']

    # Grant Request
    grant_0 = {
        'operationParam': {
            'maxEirp': 35,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }

    # Create the actual config.
    config = {
        'registrationRequest': device_b,
        'conditionalRegistrationData': [conditionals_b],
        'grantRequest': grant_0,
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_QPR_7_default_config)
  def test_WINNF_FT_S_QPR_7(self, config_filename):
    """[Configurable] Unsuccessful Grant Request from CBSDs within 4.8 km of
      the FCC Field Offices.
    """
    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'registrationRequest': dict,
            'conditionalRegistrationData': list,
            'grantRequest': dict
        })

    # Whitelist FCC ID and User ID.
    self._sas_admin.InjectFccId({
        'fccId': config['registrationRequest']['fccId']
    })
    self._sas_admin.InjectUserId({
        'userId': config['registrationRequest']['userId']
    })

    # Pre-load conditional registration data.
    if config['conditionalRegistrationData']:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    # Register CBSD.
    request = {'registrationRequest': [config['registrationRequest']]}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response.
    self.assertEqual(len(response), 1)
    if response[0]['response']['responseCode'] != 0:
      return  # SAS passes immediately in this case.
    cbsd_id = response[0]['cbsdId']
    del request, response

    # Calculate the closest FCC office
    lat_cbsd = config['conditionalRegistrationData'][0]['installationParam'][
        'latitude']
    lon_cbsd = config['conditionalRegistrationData'][0]['installationParam'][
        'longitude']
    distance_offices = [
        vincenty.GeodesicDistanceBearing(
            lat_cbsd, lon_cbsd, office['latitude'], office['longitude'])[0]
        for office in self.fcc_offices
    ]
    index_closest = np.argmin(distance_offices)
    closest_fcc_office = self.fcc_offices[index_closest]
    logging.info('Closest FCC office Lat: %f', closest_fcc_office['latitude'])
    logging.info('Closest FCC office Long: %f',
                 closest_fcc_office['longitude'])
    # Calculate bearing and ant_gain
    _, bearing, _ = vincenty.GeodesicDistanceBearing(
        lat_cbsd, lon_cbsd, closest_fcc_office['latitude'],
        closest_fcc_office['longitude'])
    ant_gain = antenna.GetStandardAntennaGains(
        bearing,
        config['conditionalRegistrationData'][0]['installationParam'][
            'antennaAzimuth'],
        config['conditionalRegistrationData'][0]['installationParam'][
            'antennaBeamwidth'],
        config['conditionalRegistrationData'][0]['installationParam'][
            'antennaGain']
    )
    logging.info('ant_gain is %f dBi', ant_gain)
    # Gather values required for calculating EIRP
    p = config['grantRequest']['operationParam']['maxEirp']
    logging.info('Grant maxEirp is %f', p)
    max_ant_gain = (
        config['conditionalRegistrationData'][0]['installationParam'][
            'antennaGain'])
    logging.info('max_ant_gain is %f dBi', max_ant_gain)
    bw = (
        config['grantRequest']['operationParam']['operationFrequencyRange']
        ['highFrequency'] - config['grantRequest']['operationParam']
        ['operationFrequencyRange']['lowFrequency']) / 1.e6
    logging.info('bw is %f MHz', bw)
    # Calculate EIRP to verify grant response
    eirp = (p - max_ant_gain + ant_gain + (10 * np.log10(bw)))
    logging.info('EIRP is %f dBm', eirp)

    # If successfully registered, CBSD sends a grant request
    config['grantRequest']['cbsdId'] = cbsd_id
    grant_request = config['grantRequest']
    request = {'grantRequest': [grant_request]}
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response
    self.assertEqual(len(response), 1)
    # If EIRP <= 49.15 dBm = SUCCESS
    if eirp <= 49.15:
      self.assertEqual(response[0]['response']['responseCode'], 0)
    # If EIRP > 49.15 dBm = INTERFERENCE
    else:
      self.assertEqual(response[0]['response']['responseCode'], 400)

  def generate_QPR_8_default_config(self, filename):
    """Generates the WinnForum configuration for QPR.8."""

    # Load device info
    # Cat B - between 2.4 km - 4.8 km of Waipahu, Hawaii Field Office.
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_b['installationParam']['latitude'] = 21.397934
    device_b['installationParam']['longitude'] = -158.034459

    # device_b is Category B with conditionals pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam'],
        'measCapability': device_b['measCapability']
    }
    del device_b['installationParam']
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['measCapability']

    # Grant Requests
    grant_0 = {
        'operationParam': {
            'maxEirp': 35,
            'operationFrequencyRange': {
                'lowFrequency': 3650000000,
                'highFrequency': 3660000000
            }
        }
    }
    grant_1 = {
        'operationParam': {
            'maxEirp': 35,
            'operationFrequencyRange': {
                'lowFrequency': 3660000000,
                'highFrequency': 3670000000
            }
        }
    }
    # Create the actual config.
    config = {
        'registrationRequest': device_b,
        'conditionalRegistrationData': [conditionals_b],
        'grantRequest1': grant_0,
        'grantRequest2': grant_1
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_QPR_8_default_config)
  def test_WINNF_FT_S_QPR_8(self, config_filename):
    """[Configurable] Unsuccessful Grant Request from CBSDs within 4.8 km of
      the FCC Field Offices with multiple grants.
    """
    config = loadConfig(config_filename)
    self.assertValidConfig(
        config, {
            'registrationRequest': dict,
            'conditionalRegistrationData': list,
            'grantRequest1': dict,
            'grantRequest2': dict
        })

    # Whitelist FCC ID and User ID.
    self._sas_admin.InjectFccId({
        'fccId': config['registrationRequest']['fccId']
    })
    self._sas_admin.InjectUserId({
        'userId': config['registrationRequest']['userId']
    })

    # Pre-load conditional registration data.
    if config['conditionalRegistrationData']:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    # Step 1: Register CBSD.
    request = {'registrationRequest': [config['registrationRequest']]}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response.
    self.assertEqual(len(response), 1)
    if response[0]['response']['responseCode'] != 0:
      return  # SAS passes immediately in this case.
    cbsd_id = response[0]['cbsdId']
    del request, response

    # Step 2: Request first grant.
    config['grantRequest1']['cbsdId'] = cbsd_id
    grant_request = config['grantRequest1']
    request = {'grantRequest': [grant_request]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check if the first grant response is successful.
    grant1_approved = response['response']['responseCode'] == 0
    del request, response

    # Step 3: Request second grant
    config['grantRequest2']['cbsdId'] = cbsd_id
    grant_request = config['grantRequest2']
    request = {'grantRequest': [grant_request]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check if the second grant response is successful.
    grant2_approved = response['response']['responseCode'] == 0
    del request, response

    if not (grant1_approved or grant2_approved):
      logging.info('Both grant requests were rejected')
      return  # SAS passes immediately in this case.

    # Calculate the closest FCC office
    lat_cbsd = config['conditionalRegistrationData'][0]['installationParam'][
        'latitude']
    lon_cbsd = config['conditionalRegistrationData'][0]['installationParam'][
        'longitude']
    distance_offices = [
        vincenty.GeodesicDistanceBearing(
            lat_cbsd, lon_cbsd, office['latitude'], office['longitude'])[0]
        for office in self.fcc_offices
    ]
    index_closest = np.argmin(distance_offices)
    closest_fcc_office = self.fcc_offices[index_closest]
    logging.info('Closest FCC Office Lat: %f', closest_fcc_office['latitude'])
    logging.info('Closest FCC Office Long: %f', closest_fcc_office['longitude'])
    # Calculate bearing and ant_gain
    _, bearing, _ = vincenty.GeodesicDistanceBearing(
        lat_cbsd, lon_cbsd, closest_fcc_office['latitude'],
        closest_fcc_office['longitude'])
    logging.info('Bearing: %f', bearing)
    ant_gain_dbi = antenna.GetStandardAntennaGains(
        bearing,
        config['conditionalRegistrationData'][0]['installationParam'][
            'antennaAzimuth'],
        config['conditionalRegistrationData'][0]['installationParam'][
            'antennaBeamwidth'],
        config['conditionalRegistrationData'][0]['installationParam'][
            'antennaGain']
    )
    logging.info('Ant Gain: %f dBi', ant_gain_dbi)
    max_ant_gain_dbi = (
        config['conditionalRegistrationData'][0]['installationParam'][
            'antennaGain'])
    logging.info('Max Ant Gain: %f dBi', max_ant_gain_dbi)

    # Gather values required for calculating Total EIRP
    grant1_eirp = 0
    if grant1_approved:
      p1 = config['grantRequest1']['operationParam']['maxEirp']
      logging.info('Grant 1 Max Eirp: %f dBm/MHz', p1)
      bw1 = (config['grantRequest1']['operationParam']
             ['operationFrequencyRange']['highFrequency'] -
             config['grantRequest1']['operationParam']
             ['operationFrequencyRange']['lowFrequency']) / 1.e6
      logging.info('Grant 1 Bandwidth: %f', bw1)
      grant1_eirp = (10**(p1/10.0)) * bw1
      logging.info('Grant 1 nominal EIRP is %f', grant1_eirp)

    grant2_eirp = 0
    if grant2_approved:
      p2 = config['grantRequest2']['operationParam']['maxEirp']
      logging.info('Grant 2 Max Eirp: %f dBm/MHz', p2)
      bw2 = (config['grantRequest2']['operationParam']
             ['operationFrequencyRange']['highFrequency'] -
             config['grantRequest2']['operationParam']
             ['operationFrequencyRange']['lowFrequency']) / 1.e6
      logging.info('Grant 2 Bandwidth: %f', bw2)
      grant2_eirp = (10**(p2/10.0)) * bw2
      logging.info('Grant 2 nominal EIRP is %f', grant2_eirp)

    # Step 4: Calculate Total EIRP
    total_eirp_dbm = ant_gain_dbi - max_ant_gain_dbi + (
        10 * np.log10(grant1_eirp + grant2_eirp))
    logging.info('Total EIRP is %f dBm', total_eirp_dbm)

    # CHECK: Total EIRP of all approved grants is <= 49.15 dBm
    self.assertLessEqual(total_eirp_dbm, 49.15)
