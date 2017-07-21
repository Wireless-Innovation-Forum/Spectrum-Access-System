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
import os
import sas
from util import winnforum_testcase
import sas_testcase


class EscSensorMessageExchangeTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_ESM_1(self):
    """This test verifies that a SAS can successfully responds to another 
    SAS (Test Harness) on a specific ESC sensor
    
    Response Code should be 200
    """
    # Inject the ESC Sensor Data
    esc_sensor_record = json.load(
      open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
    self._sas_admin.InjectEscSensorDataRecord({'record': esc_sensor_record})

    # Get the ESC Sensor Record using Pull Command
    response = self._sas.GetEscSensorRecord(esc_sensor_record['id'])
    # Verify the response using EscSensorRecord Object schema
    self.AssertContainsRequiredFields("EscSensorRecord.schema.json", response)
    self.assertDictEqual(esc_sensor_record, response)
