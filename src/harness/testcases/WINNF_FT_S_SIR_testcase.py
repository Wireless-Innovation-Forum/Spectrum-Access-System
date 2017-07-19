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


class ImplementationRecordExchangeTestcase(sas_testcase.SasTestCase):
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @classmethod
  def setUpClass(self):
    self._sas_server = sas.GetServer()
    self._sas_server.StartServer()

  @classmethod
  def tearDownClass(self):
    self._sas_server.StopServer()

  @winnforum_testcase
  def test_WINNF_FT_S_SIR_1(self):
    """This test verifies that a SAS can successfully respond to an implementation record 
    request from another SAS

    Response Code should be 200
    """
    # Inject the SAS Implementation Record
    impl_record = json.load(
      open(os.path.join('testcases', 'testdata', 'sas_impl_record_0.json')))
    self._sas_admin.InjectSasImplementationRecord({'record': impl_record})

    # Get the SAS Implementation Record using Pull Command
    response = self._sas.GetSasImplementationRecord(impl_record['id'])
    # Verify the response using SasImplementationMessage Object schema
    self.assertContainsRequiredFields("SasImplementationMessage.schema.json", response)
    self.assertDictEqual(impl_record, response)

  @winnforum_testcase
  def test_WINNF_FT_S_SIR_2(self):
    """This test verifies that the SAS Under Test can successfully pull a SAS Implementation 
    Record from the SAS Test Harness."""

    # Load Test Harness SAS Implementation Record
    sas_impl_record = json.load(open(os.path.join('testcases', 'testdata', 'sas_impl_record_0.json')))
    self._sas_admin.InjectSasImplementationRecord({'record': sas_impl_record})
    expected_path = '/sas_impl/%s' % sas_impl_record['id']

    # Setup the Server with response body and expected path from SAS Under Test
    response = self._sas_server.setupServer({'responseBody': sas_impl_record, 'expectedPath': expected_path})
    self._sas_admin.TriggerSasImplementationRecord({'address': self._sas_server.getBaseUrl(),
                                                    'sasImplementationId': sas_impl_record['id']})
    # Get Path and Body from the response
    path, body = response()
    # Check the Path of the Pull Command
    self.assertEqual(path, expected_path)

  @winnforum_testcase
  def test_WINNF_FT_S_SIR_3(self):
    """This test verifies that a SAS Under Test can handle the Unknown 
    Implementation Id 

    Response Code must be 200 with empty JSON Body"""

    # Get the SAS Implementation Record using Pull Command with Unknown ID
    response = self._sas.GetSasImplementationRecord('sas_impl/admin_0/unknown_id')
    # Check if the response is empty JSON Object
    self.assertEqual(response, {})
