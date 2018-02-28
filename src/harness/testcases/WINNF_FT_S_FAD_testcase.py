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
""" Implementation of FAD test cases """

import json
import os
import sas
import sas_testcase
from reference_models.geo import vincenty
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
    generatePpaRecords
from util import configurable_testcase, writeConfig, loadConfig, \
    getCertificateFingerprint, getRandomLatLongInPolygon, makePpaAndPalRecordsConsistent

class FullActivityDumpTestcase(sas_testcase.SasTestCase):
  """ This class contains all FAD related tests mentioned in SAS TS  """

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_FAD_2_default_config(self, filename):
    """Generates the WinnForum configuration for FAD_2"""
    # Create the actual config for FAD_2

    # Load the esc sensor in SAS Test Harness
    esc_sensor = json.load(open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))

    # Load the device_c1 with registration in SAS Test Harness
    device_c1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Get a latitude and longitude within 40 kms from ESC.
    latitude, longitude, _ = vincenty.GeodesicPoint(esc_sensor['installationParam']['latitude'],
                                                    esc_sensor['installationParam']['longitude'],
                                                    15,
                                                    30)  # distance of 15 kms from ESC at 30 degrees

    # Load the device_c1 in the neighborhood area of the ESC sensor
    device_c1['installationParam']['latitude'] = latitude
    device_c1['installationParam']['longitude'] = longitude

    # Load grant request for device_c1
    grant_g1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g1['operationParam']['maxEirp'] = 20

    # Load one ppa in SAS Test Harness
    pal_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000
    ppa_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))

    ppa_record_a, pal_records = makePpaAndPalRecordsConsistent(ppa_record_0,
                                                                [pal_record_0],
                                                                pal_low_frequency,
                                                                pal_high_frequency,
                                                                'test_user_1')

    # Load device_c3 in SAS Test Harness
    device_c3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    # Load the device_c3 in the neighborhood area of the PPA
    device_c3['installationParam']['latitude'] = 38.821322
    device_c3['installationParam']['longitude'] = -97.282813

    # Load grant request for device_c3 in SAS Test Harness
    grant_g3 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g3['operationParam']['maxEirp'] = 20

    # Update grant_g3 frequency to overlap with PPA zone frequency for C3 device
    grant_g3['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3550000000,
        'highFrequency': 3555000000
    }

    # Load the device_c2 with registration to SAS UUT
    device_c2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Get a latitude and longitude within 40 kms from ESC.
    latitude, longitude, _ = vincenty.GeodesicPoint(esc_sensor['installationParam']['latitude'],
                                         esc_sensor['installationParam']['longitude'], 20,
                                         30)  # distance of 20 kms from ESC at 30 degrees

    device_c2['installationParam']['latitude'] = latitude
    device_c2['installationParam']['longitude'] = longitude

    # Creating conditionals for C2 and C4.
    self.assertEqual(device_c2['cbsdCategory'], 'B')
    conditional_parameters_c2 = {
        'cbsdCategory': device_c2['cbsdCategory'],
        'fccId': device_c2['fccId'],
        'cbsdSerialNumber': device_c2['cbsdSerialNumber'],
        'airInterface': device_c2['airInterface'],
        'installationParam': device_c2['installationParam'],
        'measCapability': device_c2['measCapability']
    }
    del device_c2['cbsdCategory']
    del device_c2['airInterface']
    del device_c2['installationParam']

    # Load grant request for device_c2 to SAS UUT
    grant_g2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g2['operationParam']['maxEirp'] = 30

    # Load the device_c4 with registration to SAS UUT.
    device_c4 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))

    # Move device_c4 in the neighborhood area of the PPA
    device_c4['installationParam']['latitude'] = 38.805335
    device_c4['installationParam']['longitude'] = -97.307623

    # Creating conditionals for Cat B devices.
    self.assertEqual(device_c4['cbsdCategory'], 'B')
    conditional_parameters_c4 = {
        'cbsdCategory': device_c4['cbsdCategory'],
        'fccId': device_c4['fccId'],
        'cbsdSerialNumber': device_c4['cbsdSerialNumber'],
        'airInterface': device_c4['airInterface'],
        'installationParam': device_c4['installationParam'],
        'measCapability': device_c4['measCapability']
    }
    del device_c4['cbsdCategory']
    del device_c4['airInterface']
    del device_c4['installationParam']

    # Load grant request for device_c4 to SAS UUT
    grant_g4 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g4['operationParam']['maxEirp'] = 20

    #Update grant_g4 frequency to overlap with PPA zone frequency for C4 device
    grant_g4['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3550000000,
        'highFrequency': 3555000000
    }

    conditional_parameters = {
        'registrationData': [conditional_parameters_c2,
                             conditional_parameters_c4]
    }

    cbsd_records = [device_c1, device_c3]
    grant_record_list = [[grant_g1], [grant_g3]]
    ppa_records = [ppa_record_a]
    cbsd_reference_ids = [['cbsdId-1', 'cbsdId-2']]

    # SAS test harness configuration
    sas_harness_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': 'localhost',
        'port': 9001,
        'serverCert': "certs/server.cert",
        'serverKey': "certs/server.key",
        'caCert': "certs/ca.cert"
    }
    # Generate FAD Records for each record type like cbsd,zone and esc_sensor
    cbsd_fad_records = generateCbsdRecords(cbsd_records, grant_record_list)
    ppa_fad_record = generatePpaRecords(ppa_records, cbsd_reference_ids)
    esc_fad_record = [esc_sensor]

    sas_harness_dump_records = {
        'cbsdRecords': cbsd_fad_records,
        'ppaRecord': ppa_fad_record,
        'escSensorRecord': esc_fad_record
    }
    config = {
        'registrationRequestC2': device_c2,
        'registrationRequestC4': device_c4,
        'conditionals': conditional_parameters,
        'grantRequestG2': grant_g2,
        'grantRequestG4': grant_g4,
        'palRecords': pal_records[0],
        'sasTestHarnessConfig': sas_harness_config,
        'sasTestHarnessConfigDumpRecords': sas_harness_dump_records
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FAD_2_default_config)
  def test_WINNF_FT_S_FAD_2(self, config_filename):
    """Full Activity Dump Pull Command by SAS UUT.

    Checks SAS UUT can successfully request a Full Activity Dump and utilize
    the retrieved data.
    Checks SAS UUT responds with HeartbeatResponse either GRANT_TERMINATED or INVALID_VALUE,
    indicating a terminated Grant.

    """

    config = loadConfig(config_filename)

    device_c2 = config['registrationRequestC2']
    device_c4 = config['registrationRequestC4']
    grant_g2 = config['grantRequestG2']
    grant_g4 = config['grantRequestG4']
    sas_test_harness_dump_records = [config['sasTestHarnessConfigDumpRecords']['cbsdRecords'],
                                     config['sasTestHarnessConfigDumpRecords']['ppaRecord'],
                                     config['sasTestHarnessConfigDumpRecords']['escSensorRecord']]

    # Initialize SAS Test Harness Server instance to dump FAD records
    sas_test_harness = SasTestHarnessServer(config['sasTestHarnessConfig']['sasTestHarnessName'],
                                            config['sasTestHarnessConfig']['hostName'],
                                            config['sasTestHarnessConfig']['port'],
                                            config['sasTestHarnessConfig']['serverCert'],
                                            config['sasTestHarnessConfig']['serverKey'],
                                            config['sasTestHarnessConfig']['caCert'])
    sas_test_harness.writeFadRecords(sas_test_harness_dump_records)
    # Start the server
    sas_test_harness.start()

    # Whitelist the FCCID and UserID for CBSD C2 in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_c2['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c2['userId']})

    # Whitelist the FCCID and UserID for CBSD C4 in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_c4['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c4['userId']})

    # Whitelist the FCCID and UserID of the devices loaded to SAS-test_harness in SAS UUT
    for cbsdRecord in config['sasTestHarnessConfigDumpRecords']['cbsdRecords']:
      self._sas_admin.InjectFccId({'fccId': cbsdRecord['registration']['fccId']})


    # Register devices C2 and C4, request grants G2 and G4 respectively with SAS UUT.
    # Ensure the registration and grant requests are successful.
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted([device_c2, device_c4],
                                                          [grant_g2, grant_g4],
                                                          config['conditionals'])

    # Send the Heartbeat request for the Grant G2 and G4 of CBSD C2 and C4
    # respectively to SAS UUT.
    transmit_expire_times = self.assertHeartbeatsSuccessful(cbsd_ids, grant_ids,
                                      [[('GRANTED')],[('GRANTED')]])

    # Notify the SAS UUT about the SAS Test Harness
    certificate_hash = getCertificateFingerprint(config['sasTestHarnessConfig']['serverCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': sas_test_harness.getBaseUrl()})

    # Injecting the PAL Records of the PPA into SAS UUT.
    self._sas_admin.InjectPalDatabaseRecord(config['palRecords'])

    # Trigger CPAS in the SAS UUT and wait until complete.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Send the Heartbeat request again for the G2 and G4 to SAS UUT
    request = {
        'heartbeatRequest': [
            {
                'cbsdId': cbsd_ids[0],
                'grantId': grant_ids[0],
                'operationState': 'GRANTED'
            },
            {
                'cbsdId': cbsd_ids[1],
                'grantId': grant_ids[1],
                'operationState': 'GRANTED'
            }
        ]}
    response = self._sas.Heartbeat(request)['heartbeatResponse']

    # Check the length of request and response match.
    self.assertEqual(len(request['heartbeatRequest']), len(response))

    # Check grant response, must be response code 0.
    for resp in response:
      self.assertTrue(resp['response']['responseCode'] in (103, 500))

    # Stop SAS Test Harness and clean up.
    sas_test_harness.shutdown()
    del sas_test_harness