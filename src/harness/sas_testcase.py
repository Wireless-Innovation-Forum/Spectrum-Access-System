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
"""Implementation of SasTestcaseInterface"""

import json
from jsonschema import validate, Draft4Validator, RefResolver
import os
import unittest
import sas_interface


class SasTestCase(sas_interface.SasTestcaseInterface, unittest.TestCase):

  def AssertContainsRequiredFields(self, schema_filename, response):
    schema_filename = os.path.join('..', '..', 'schema', schema_filename)
    schema = json.load(open(schema_filename))
    Draft4Validator.check_schema(schema)
    schema_dir = os.path.dirname(os.path.realpath(schema_filename))
    resolver = RefResolver(referrer=schema, base_uri='file://' + schema_dir + '/')
    # Raises ValidationError when incorrect response
    validate(response, schema, resolver=resolver)