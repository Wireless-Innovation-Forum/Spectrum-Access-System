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

  def AssertValidResponseFormatForApprovedGrant(self, grant_response):
    """Validate an approved grant response.

    Check presence and basic validity of each required field.
    Check basic validity of optional fields if they exist.
    Args:
      grant_response: A dictionary with a single grant response object from an
        array originally returned by a SAS server as specified in TS

    Returns:
      Nothing. It asserts if something about the response is broken/not per
      specs. Assumes it is dealing with an approved request.
    """
    # Check required string fields
    for field_name in ('cbsdId', 'grantId', 'grantExpireTime', 'channelType'):
      self.assertTrue(field_name in grant_response)
      self.assertGreater(len(grant_response[field_name]), 0)

    self.assertTrue('heartbeatInterval' in grant_response)

    if 'measReportConfig' in grant_response:
      self.assertGreater(len(grant_response['measReportConfig']), 0)

    # operationParam should not be set if grant is approved
    self.assertFalse('operationParam' in grant_response)
    self.assertTrue(grant_response['channelType'] in ('PAL', 'GAA'))
