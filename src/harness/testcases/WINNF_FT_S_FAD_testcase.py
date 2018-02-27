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
from sas_test_harness import SasTestHarnessServer
from util import configurable_testcase, writeConfig, loadConfig, getCertFilename,\
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
    device_c1['installationParam']['latitude'] = latitude
    device_c1['installationParam']['longitude'] = longitude

    # Load grant request for device_c1
    grant_g1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g1['operationParam']['maxEirp'] = 20

    # Load one ppa in SAS Test Harness
    pal_record_a = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000
    ppa_record_a = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record_a, pal_record_a = makePpaAndPalRecordsConsistent(ppa_record_a,
                                                                [pal_record_a],
                                                                pal_low_frequency,
                                                                pal_high_frequency,
                                                                'test_user_1')

    # Load device_c3 within the PPA in SAS Test Harness
    device_c3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c3['installationParam']['latitude'] = 38.822321
    device_c3['installationParam']['longitude'] = -97.283932

    # Load grant request for device_c3 in SAS Test Harness
    grant_g3 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g3['cbsdId'] = device_c3['userId']
    grant_g3['operationParam']['maxEirp'] = 20

    # Update grant_G3 frequency to overlap with PPA zone frequency for C3 device
    grant_g3['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3550000000,
        'highFrequency': 3555000000
    }

    # Load the device_c2 with registration to SAS UUT
    device_c2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    # Load grant request for device_c2 to SAS UUT
    grant_g2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g2['operationParam']['maxEirp'] = 30

    # Get a latitude and longitude within 40 kms from ESC.
    latitude, longitude, _ = vincenty.GeodesicPoint(esc_sensor['installationParam']['latitude'],
                                         esc_sensor['installationParam']['longitude'], 20,
                                         30)  # distance of 20 kms from ESC at 30 degrees

    device_c2['installationParam']['latitude'] = latitude
    device_c2['installationParam']['longitude'] = longitude

    # Load the device_c4 with registration to SAS UUT.
    device_c4 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))

    #Placing this device within the PPA
    device_c4['installationParam']['latitude'] = 38.7790
    device_c4['installationParam']['longitude'] = -97.2263

    # Load grant request for device_c4 to SAS UUT
    grant_g4 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_g4['operationParam']['maxEirp'] = 20

    #Update grant_G4 frequency to overlap with PPA zone frequency for C4 device
    grant_g4['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3555000000,
        'highFrequency': 3560000000
    }

    cbsd_records = [device_c1, device_c3]
    grant_record_list = [[grant_g1], [grant_g3]]
    ppa_records = [ppa_record_a]
    cbsdIds_reference_id_list = [['cbsdId-1', 'cbsdId-2']]

    # SAS test harness configuration
    sas_harness_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': 'localhost',
        'port': 9001,
        'sasVersion': 'v1.2',
        'serverCert': getCertFilename("server.cert"),
        'serverKey': getCertFilename("server.key"),
        'fileServePath': '/home/cbrsdev/FAD2/data'
    }

    # Generate FAD Records for each record type like cbsd,zone and esc_sensor
    cbsd_fad_records = SasTestHarnessServer.generateCbsdRecords(cbsd_records, grant_record_list)
    ppa_fad_record = SasTestHarnessServer.generatePpaRecords(ppa_records, cbsdIds_reference_id_list)
    esc_fad_record = [esc_sensor]

    sas_harness_dump_records = {
        'cbsdRecords': cbsd_fad_records,
        'ppaRecord': ppa_fad_record,
        'escSensorRecord': esc_fad_record
    }
    config = {
        'registrationRequestC2': device_c2,
        'registrationRequestC4': device_c4,
        'grantRequestG2': grant_g2,
        'grantRequestG4': grant_g4,
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
    sas_test_harness_config = config['sasTestHarnessConfig']
    device_c2 = config['registrationRequestC2']
    device_c4 = config['registrationRequestC4']
    grant_g2 = config['grantRequestG2']
    grant_g4 = config['grantRequestG4']
    sas_test_harness_dump_records_config = config['sasTestHarnessConfigDumpRecords']
    sas_test_harness_dump_records = [sas_test_harness_dump_records_config['cbsdRecords'],
                                     sas_test_harness_dump_records_config['ppaRecord'],
                                     sas_test_harness_dump_records_config['escSensorRecord']]

    sas_harness_base_url = "https://" + sas_test_harness_config['hostName'] + ':' + \
                      str(sas_test_harness_config['port']) + '/' + \
                      sas_test_harness_config['sasVersion']

    # Initialize SAS Test Harness Server instance to dump FAD records
    sas_test_harness = SasTestHarnessServer(sas_test_harness_config['sasTestHarnessName'],
                                            sas_test_harness_config['hostName'],
                                            sas_test_harness_config['port'],
                                            sas_test_harness_config['sasVersion'],
                                            sas_test_harness_config['fileServePath'],
                                            sas_test_harness_config['serverCert'],
                                            sas_test_harness_config['serverKey'])

    SasTestHarnessServer.writeFadRecords(sas_harness_base_url,
                                         sas_test_harness_config['fileServePath'],
                                         sas_test_harness_dump_records)
    # Start the server
    sas_test_harness.start()

    # Whitelist the FCCID and UserID for CBSD C2 in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_c2['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c2['userId']})

    # Whitelist the FCCID and UserID for CBSD C4 in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_c4['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c4['userId']})

    # Whitelist the FCCID and UserID of the devices loaded to SAS-test_harness in SAS UUT
    for cbsdRecord in sas_test_harness_dump_records_config['cbsdRecords']:
      self._sas_admin.InjectFccId({'fccId': cbsdRecord['registration']['fccId']})
      self._sas_admin.InjectUserId({'userId': cbsdRecord['registration']['userId']})

    # Send a valid Registration Request for CBSD (C2) to the SAS UUT
    # Check registration response of SAS UUT
    # Send a valid Grant Request Message for CBSD (G2) to the SAS UUT
    # Check grant response of G2 from SAS UUT

    cbsd_ids_c2, grant_ids_c2 = self.assertRegisteredAndGranted([device_c2], [grant_g2])

    # Send a valid Registration Request for CBSD (C4) to the SAS UUT
    # Check registration response  of SAS UUT
    # Send a valid Grant Request for CBSD (G4) to SAS UUT
    # Check grant response of G4 from SAS UUT

    cbsd_ids_c4, grant_ids_c4 = self.assertRegisteredAndGranted([device_c4], [grant_g4])

    # Send the Heartbeat request for the Grant G2 and G4 of CBSD C2 and C4
    #                                    to SAS UUT
    transmit_expire_times = self.assertHeartbeatsSuccessful(
        list([cbsd_ids_c2, cbsd_ids_c4]),
        list([grant_ids_c2, grant_ids_c4]),
        list([[('GRANTED')], [('GRANTED')]])
    )

    # Notify the SAS UUT about the SAS Test Harness
    certificate_hash = getCertificateFingerprint(sas_test_harness_config['serverCert'])
    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': sas_harness_base_url})

    # Trigger CPAS in the SAS UUT and wait until complete.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Send the Heartbeat request again for the G2 and G4 to SAS UUT
    request = {
        'heartbeatRequest': [
            {
                'cbsdId': cbsd_ids_c2[0],
                'grantId': grant_ids_c2[0],
                'operationState': 'GRANTED'
            },
            {
                'cbsdId': cbsd_ids_c4[0],
                'grantId': grant_ids_c4[0],
                'operationState': 'GRANTED'
            }
        ]}
    responses = self._sas.Heartbeat(request)['heartbeatResponse']
    for response in responses:
      self.assertTrue(response['response']['responseCode'] in (103, 500))

    sas_test_harness.shutdown()
    del sas_test_harness
