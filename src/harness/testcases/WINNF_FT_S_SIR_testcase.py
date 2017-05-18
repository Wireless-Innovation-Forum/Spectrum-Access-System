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
import unittest
import sas
from util import winnforum_testcase
from jsonschema import validate, Draft4Validator, ValidationError, RefResolver


class ImplementationRecordExchangeTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

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
    response = self._sas.ImplementationRecordExchange(impl_record['id'])

    # Verify the response using SasImplementationMessage Object schema
    schema_path = os.path.join('..', '..', 'schema', 'SasImplementationMessage.schema.json')
    schema = json.load(open(schema_path))
    Draft4Validator.check_schema(schema)
    schema_directory = os.path.dirname(os.path.realpath(schema_path))
    resolver = RefResolver(referrer=schema, base_uri='file://' + schema_directory + '/')
    # Validate with schema
    self.assertRaises(ValidationError, validate(response, schema, resolver=resolver))








