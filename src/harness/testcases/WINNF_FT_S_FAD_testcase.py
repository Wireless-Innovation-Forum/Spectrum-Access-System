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
from sas_test_harness import SasTestHarnessServer
from util import configurable_testcase, writeConfig, loadConfig, getCertFilename,\
    getCertificateFingerprint, getRandomLatLongInPolygon, makePpaAndPalRecordsConsistent

class FullActivityDumpTestcase(sas_testcase.SasTestCase):
  """ This class contains all FAD related tests mentioned in SAS TS  """

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()
    self._sas_server = None

  def tearDown(self):
    if hasattr(self, '_sas_server'):
      self._sas_server.shutdown()

  def generate_FAD_2_default_config(self, filename):
    """Generates the WinnForum configuration for FAD_2"""
    # Create the actual config for FAD_2

    # Step 1: Load the esc sensor in SAS Test Harness
    esc_sensor = json.load(open(os.path.join('testcases', 'testdata', 'esc_sensor_record_1.json')))

    # Step 2: Load the device_a with registration in SAS Test Harness
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Step 2: Load grant request for device_a
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_a['operationParam']['maxEirp'] = 20

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
    # Load device_c within the PPA in SAS Test Harness
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    latitude, longitude = getRandomLatLongInPolygon(ppa_record_a)
    device_c['installationParam']['latitude'] = round(latitude, 6)
    device_c['installationParam']['longitude'] = round(longitude, 6)

    # Load grant request for device_c in SAS Test Harness
    grant_c = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_c['cbsdId'] = device_c['userId']
    grant_c['operationParam']['maxEirp'] = 20

    # Load the device_e with registration to SAS UUT
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    # Load grant request for device_e to SAS UUT
    grant_e = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_e['operationParam']['maxEirp'] = 30

    # Load device_f within the PPA to SAS UUT
    device_f = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))
    device_f['installationParam']['latitude'] = 38.7790
    device_f['installationParam']['longitude'] = -97.2263

    # Load grant request for device_f to SAS UUT
    grant_f = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_f['operationParam']['maxEirp'] = 20

    sas_harness_dump_records = {
        'cbsdRecords': [device_a, device_c],
        'grantRecords': [[grant_a], [grant_c]],
        'ppaRecords': [ppa_record_a],
        'escSensorRecords': [esc_sensor]
    }
    sas_harness_config = {
        'sasTHName': 'SAS-TH-1',
        'url': 'https://localhost:9002/v1.2',
        'serverCert': getCertFilename("server.cert"),
        'serverKey': getCertFilename("server.key"),
        'fileServePath': 'data/'
    }
    config = {
        'registrationRequestC2': device_e,
        'registrationRequestC4': device_f,
        'grantRequestC2': grant_e,
        'grantRequestC4': grant_f,
        'sasHarness': sas_harness_config,
        'sasHarnessDumpRecords': sas_harness_dump_records
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
    sas_th_config = config['sasHarness']
    device_c2 = config['registrationRequestC2']
    device_c4 = config['registrationRequestC4']
    grant_c2 = config['grantRequestC2']
    grant_c4 = config['grantRequestC4']
    sas_th_dump_records = config['sasHarnessDumpRecords']
    # Initialize SAS-TH Server instance to dump FAD records
    self._sas_server = SasTestHarnessServer(sas_th_config['sasTHName'],
                                            sas_th_config['url'],
                                            sas_th_config['fileServePath'],
                                            sas_th_config['serverCert'],
                                            sas_th_config['serverKey'])
    # Start the server
    self._sas_server.start()

    # Step 3: Whitelist the FCCID and UserID for CBSD C2 in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_c2['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c2['userId']})

    # Whitelist the FCCID and UserID for CBSD C4 in SAS UUT
    self._sas_admin.InjectFccId({'fccId': device_c4['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c4['userId']})

    # Step 4: Send a valid Registration Request for CBSD (C2) to the SAS UUT
    # Check registration response of SAS UUT
    # Step 5: Send a valid Grant Request Message for CBSD (G2) to the SAS UUT
    # Check grant response of G2 from SAS UUT

    cbsd_ids_c2, grant_ids_c2 = self.assertRegisteredAndGranted([device_c2], [grant_c2])

    # Step 8: Send a valid Registration Request for CBSD (C4) to the SAS UUT
    # Check registration response  of SAS UUT
    # Step 9: Send a valid Grant Request for CBSD (G4) to SAS UUT
    # Check grant response of G4 from SAS UUT

    cbsd_ids_c4, grant_ids_c4 = self.assertRegisteredAndGranted([device_c4], [grant_c4])

    # Step 10: Send the Heartbeat request for the Grant G2 and G4 of CBSD C2 and C4
    #                                    to SAS UUT
    transfer_expiry_timers = self.assertHeartbeatsSuccessful(
        list([cbsd_ids_c2, cbsd_ids_c4]),
        list([grant_ids_c2, grant_ids_c4]),
        list([[('GRANTED')], [('GRANTED')]])
    )

    # Create an activity dump in SAS Test Harness in local
    self._sas_server.generateFadRecords(sas_th_dump_records['cbsdRecords'],
                                        sas_th_dump_records['grantRecords'],
                                        sas_th_dump_records['ppaRecords'],
                                        sas_th_dump_records['escSensorRecords'])

    # Step 11: Notify the SAS UUT about the SAS Test Harness
    certificate_hash = getCertificateFingerprint(sas_th_config['serverCert'])

    self._sas_admin.InjectPeerSas({'certificateHash': certificate_hash,
                                   'url': sas_th_config['url'] + '/dump'})

    # Step 12: Trigger CPAS in the SAS UUT and wait until complete.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 13: Send the Heartbeat request again for the G2 and G4 to SAS UUT
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
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    self.assertTrue(response['response']['responseCode'] in (103, 500))
