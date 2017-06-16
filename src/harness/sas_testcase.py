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
import sas


class SasTestCase(sas_interface.SasTestcaseInterface, unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def assertContainsRequiredFields(self, schema_filename, response):
    schema_filename = os.path.join('..', '..', 'schema', schema_filename)
    schema = json.load(open(schema_filename))
    Draft4Validator.check_schema(schema)
    schema_dir = os.path.dirname(os.path.realpath(schema_filename))
    resolver = RefResolver(referrer=schema, base_uri='file://' + schema_dir + '/')
    # Raises ValidationError when incorrect response
    validate(response, schema, resolver=resolver)

  def assertValidResponseFormatForApprovedGrant(self, grant_response):
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

  def assertRegistered(self, registration_request,
                       conditional_registration_data=None):
    for device in registration_request:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
    if conditional_registration_data:
      self._sas_admin.PreloadRegistrationData(conditional_registration_data)

    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']

    # Check the registration response; collect CBSD IDs
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      self.assertTrue('cbsdId' in resp)
      cbsd_ids.append(resp['cbsdId'])

    # Return list of cbsd_ids
    return cbsd_ids

  def assertRegisteredAndGranted(self, registration_request, grant_request,
                                 conditional_registration_data=None):
    self.assertEqual(len(registration_request), len(grant_request))
    cbsd_ids = self.assertRegistered(registration_request,
                                     conditional_registration_data)
    list_of_cbsd_ids_and_grant_ids = []

    for cbsd_id, grant_req in zip(cbsd_ids, grant_request):
      grant_req['cbsdId'] = cbsd_id

    request = {'grantRequest': grant_request}
    grant_response = self._sas.Grant(request)['grantResponse']

    # Check the grant response; collect CBSD and Grant IDs
    for cbsd_id, grant_resp in zip(cbsd_ids, grant_response):
      self.assertEqual(grant_resp['cbsdId'], cbsd_id)
      self.assertTrue(grant_resp['grantId'])
      self.assertEqual(grant_resp['response']['responseCode'], 0)

      list_of_cbsd_ids_and_grant_ids.append({
          'cbsdId': grant_resp['cbsdId'],
          'grantId': grant_resp['grantId']
      })

    # Return cbsd_ids and grant_ids
    return list_of_cbsd_ids_and_grant_ids
