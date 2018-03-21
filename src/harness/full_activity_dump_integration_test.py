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
"""Request handler test case"""

import unittest
import json
import os
import mock
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, generateCbsdReferenceId, generatePpaRecords
from util import makePpaAndPalRecordsConsistent
from full_activity_dump_helper import getFullActivityDumpSasTestHarness, getFullActivityDumpSasUut
from functools import partial
from datetime import datetime


class FullActivityDumpIntegrationTest(unittest.TestCase):
  """Full Activity Dump integration tests.

  Tests that the FAD collection pipeline is functional. FAD data is requested
  from test harnesses via HTTPS and used to generate FAD objects.
  """

  def setUp(self):
    cbsd_records = [
        json.load(open(os.path.join('testcases', 'testdata', 'device_a.json'))),
        json.load(open(os.path.join('testcases', 'testdata', 'device_b.json'))),
        json.load(open(os.path.join('testcases', 'testdata', 'device_c.json')))
    ]
    grant_records = [[
        json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    ], [
        json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    ], [json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))]]
    cbsd_fad_records = generateCbsdRecords(cbsd_records, grant_records)

    pal_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_low_frequency = 3550000000
    pal_high_frequency = 3560000000
    ppa_record_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
    ppa_record_a, pal_records = makePpaAndPalRecordsConsistent(
        ppa_record_0, [pal_record_0], pal_low_frequency, pal_high_frequency,
        'test_user_1')
    ppa_records = [ppa_record_a]
    cbsd_reference_ids = [[
        generateCbsdReferenceId('test_fcc_id_x', 'test_serial_number_x'),
        generateCbsdReferenceId('test_fcc_id_y', 'test_serial_number_y')
    ]]
    ppa_fad_records = generatePpaRecords(ppa_records, cbsd_reference_ids)

    esc_fad_records = [
        json.load(
            open(
                os.path.join('testcases', 'testdata',
                             'esc_sensor_record_0.json')))
    ]
    self._test_data = [cbsd_fad_records, ppa_fad_records, esc_fad_records]

  @staticmethod
  def getFullActivityDumpHelper(ssl_cert, ssl_key, sas_interface):
    """Method to get the full activity dump but with timestamp modified to now."""
    output = sas_interface.GetFullActivityDump(ssl_cert, ssl_key)
    output['generationDateTime'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    return output

  def test_download_from_test_harness_gets_data(self):
    ssl_cert = 'certs/client.cert'
    ssl_key = 'certs/client.key'

    sas_test_harness = SasTestHarnessServer('SAS-TH-1', 'localhost', 9001,
                                            'certs/server.cert',
                                            'certs/server.key', 'certs/ca.cert')
    sas_test_harness.writeFadRecords(self._test_data)
    sas_test_harness.start()
    fad = getFullActivityDumpSasTestHarness(
        sas_test_harness.getSasTestHarnessInterface(), ssl_cert, ssl_key)

    # Testing for exact contents would be long and verbose, and also handled by
    # the FAD object, just test all the fields have something.
    self.assertNotEqual(len(fad.getCbsdRecords()), 0)
    self.assertNotEqual(len(fad.getEscSensorRecords()), 0)
    self.assertNotEqual(len(fad.getZoneRecords()), 0)

    sas_test_harness.shutdown()
    del sas_test_harness

  def test_download_from_sas_uut_gets_data(self):
    """Tests fetching from the SAS UUT """
    ssl_cert = 'certs/client.cert'
    ssl_key = 'certs/client.key'

    # Use a test harness as a fake SAS UUT.
    sas_test_harness = SasTestHarnessServer('SAS-TH-1', 'localhost', 9002,
                                            'certs/server.cert',
                                            'certs/server.key', 'certs/ca.cert')
    sas_test_harness.writeFadRecords(self._test_data)
    sas_test_harness.start()
    sas_admin = mock.MagicMock()
    sas_interface = sas_test_harness.getSasTestHarnessInterface()
     # GetFullActivityDump must be mocked to give timestamp at current time.
    sas_interface.GetFullActivityDump = mock.MagicMock()
    sas_interface.GetFullActivityDump.side_effect = partial(
        FullActivityDumpIntegrationTest.getFullActivityDumpHelper,
        sas_interface=sas_test_harness.getSasTestHarnessInterface())
    fad = getFullActivityDumpSasUut(sas_interface, sas_admin, ssl_cert, ssl_key)

    sas_admin.TriggerFullActivityDump.assert_called_once()
    # Testing for exact contents would be long and verbose, and also handled by
    # the FAD object, just test all the fields have something.
    self.assertNotEqual(len(fad.getCbsdRecords()), 0)
    self.assertNotEqual(len(fad.getEscSensorRecords()), 0)
    self.assertNotEqual(len(fad.getZoneRecords()), 0)

    sas_test_harness.shutdown()
    del sas_test_harness

  def test_download_functions_equivalent(self):
    """When the SAS UUT and test harness have the same data the FAD content should be equal."""

    ssl_cert = 'certs/client.cert'
    ssl_key = 'certs/client.key'

    # Get SAS UUT FAD.
    # Use a test harness as a fake SAS UUT.
    sas_uut = SasTestHarnessServer('SAS-TH-1', 'localhost', 9003,
                                   'certs/server.cert', 'certs/server.key',
                                   'certs/ca.cert')
    sas_uut.writeFadRecords(self._test_data)
    sas_uut.start()
    sas_admin = mock.MagicMock()
    # sas_interface must be mocked to give timestamp at current time.
    sas_interface = sas_uut.getSasTestHarnessInterface()
    sas_interface.GetFullActivityDump = mock.MagicMock()
    sas_interface.GetFullActivityDump.side_effect = partial(
        FullActivityDumpIntegrationTest.getFullActivityDumpHelper,
        sas_interface=sas_uut.getSasTestHarnessInterface())
    uut_fad = getFullActivityDumpSasUut(sas_interface, sas_admin, ssl_cert,
                                        ssl_key)

    # Get SAS test harness FAD.
    sas_test_harness = SasTestHarnessServer('SAS-TH-1', 'localhost', 9004,
                                            'certs/server.cert',
                                            'certs/server.key', 'certs/ca.cert')
    sas_test_harness.writeFadRecords(self._test_data)
    sas_test_harness.start()
    test_harness_fad = getFullActivityDumpSasTestHarness(
        sas_test_harness.getSasTestHarnessInterface(), ssl_cert, ssl_key)

    self.assertDictEqual(uut_fad.getData(), test_harness_fad.getData())

    sas_uut.shutdown()
    sas_test_harness.shutdown()
    del sas_uut
    del sas_test_harness
