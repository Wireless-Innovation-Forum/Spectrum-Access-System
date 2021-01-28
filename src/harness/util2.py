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
"""Generic helper functions for test harness."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import defaultdict
from datetime import datetime
import inspect
import json
import os
import uuid

import jsonschema


def makePalRecordsConsistent(pal_records, low_frequency, high_frequency,
                             user_id, fcc_channel_id="1",
                             start_date=None, end_date=None):
  """Make Pal object consistent with the inputs

    Args:
      pal_records: (list) A list of PAL Records in the form of dictionary.
      low_frequency: (number) The Primary Low Frequency in Hz for PAL.
      high_frequency: (number) The Primary High Frequency in Hz for PAL.
      user_id: (string) The userId to put in PAL Records.
      fcc_channel_id: (string) The FCC-supplied frequency channel identifier.
      start_date: (string) PAL license start date, generally set as one year
      before the current date
      end_date: (string) PAL license expiration date, generally set as more than
      one year after the current date
    Returns:
      A list containing individual PAL records in the form of dictionary
    Note: The PAL Dictionary must contain censusYear(number) and
          fipsCode(number)
  """
  start_date = datetime.now().replace(year=datetime.now().year - 1) \
    if start_date is None else start_date
  end_date = datetime.now().replace(year=datetime.now().year + 1) \
    if end_date is None else end_date

  for index, pal_rec in enumerate(pal_records):
    pal_fips_code = pal_rec['fipsCode']
    pal_census_year = pal_rec['censusYear']
    del pal_rec['fipsCode'], pal_rec['censusYear']

    pal_rec = defaultdict(lambda: defaultdict(dict), pal_rec)
    # Change the FIPS Code and Registration Date-Year in Pal Id
    pal_rec['palId'] = '/'.join(['pal', '%s-%d' %
                                 ('{:02d}'.format(start_date.month),
                                  start_date.year),
                                 str(pal_fips_code), fcc_channel_id])
    pal_rec['userId'] = user_id
    # Make the date consistent in Pal Record for Registration and License
    pal_rec['registrationInformation']['registrationDate'] = \
      start_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Change License Information in Pal
    pal_rec['license']['licenseAreaIdentifier'] = str(pal_fips_code)
    pal_rec['license']['licenseAreaExtent'] = \
      'zone/census_tract/census/{}/{}'.format(pal_census_year, pal_fips_code)
    pal_rec['license']['licenseDate'] = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    pal_rec['license']['licenseExpiration'] = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    pal_rec['license']['licenseFrequencyChannelId'] = fcc_channel_id
    # Change Frequency Information in Pal
    pal_rec['channelAssignment']['primaryAssignment']['lowFrequency'] = low_frequency
    pal_rec['channelAssignment']['primaryAssignment']['highFrequency'] = high_frequency
    # Converting from defaultdict to dict
    pal_records[index] = json.loads(json.dumps(pal_rec))
  return pal_records


def makePpaAndPalRecordsConsistent(ppa_record, pal_records, low_frequency,
                                   high_frequency, user_id,
                                   fcc_channel_id="1"):
  """Make PPA and PAL object consistent with the inputs

    Args:
      ppa_record: (dictionary) A dictionary containing PPA Record.
      pal_records: (list) A list of PAL Records in the form of dictionary
      which has to be associated with the PPA.
      low_frequency: (number) The Primary Low Frequency in Hz for PAL.
      high_frequency: (number) The Primary High Frequency in Hz for PAL.
      user_id: (string) The userId from the CBSD.
      fcc_channel_id: (string) The FCC-supplied frequency channel identifier.

    Returns:
      A tuple containing PPA record which itself is a dictionary and PAL records
      list which contains individual PAL records in the form of dictionary.
    Note: The PAL Dictionary must contain censusYear(number) and
          fipsCode(number)
  """
  start_date = datetime.now().replace(year=datetime.now().year - 1)
  end_date = datetime.now().replace(year=datetime.now().year + 1)

  pal_records = makePalRecordsConsistent(pal_records, low_frequency,
                                         high_frequency, user_id,
                                         fcc_channel_id, start_date, end_date)
  # Add PAL Ids into the PPA Record
  ppa_record = defaultdict(lambda: defaultdict(dict), ppa_record)

  ppa_record['ppaInfo']['palId'] = [pal['palId'] for pal in pal_records]
  ppa_record['id'] = 'zone/ppa/%s/%s/%s' % (ppa_record['creator'],
                                            ppa_record['ppaInfo']['palId'][0],
                                            uuid.uuid4().hex)

  # Make the date consistent in PPA Record
  ppa_record['ppaInfo']['ppaBeginDate'] = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
  ppa_record['ppaInfo']['ppaExpirationDate'] = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
  # Converting from defaultdict to dict
  ppa_record = json.loads(json.dumps(ppa_record))

  return ppa_record, pal_records


def assertContainsRequiredFields(schema_filename, response):
  schema_dir = os.path.abspath(os.path.join(os.path.dirname(
      inspect.getfile(inspect.currentframe())), '..', '..', 'schema'))
  schema_filename = os.path.join(schema_dir, schema_filename)
  with open(schema_filename, 'rb') as fd:
    schema = json.load(fd)
  jsonschema.Draft4Validator.check_schema(schema)
  if os.name == 'nt':
    os_base_uri = 'file:///'
  else:
    os_base_uri = 'file://'
  resolver = jsonschema.RefResolver(referrer=schema, base_uri=os_base_uri + schema_dir + '/')
  # Raises ValidationError when incorrect response
  jsonschema.validate(response, schema, resolver=resolver)


def CreateConditionalsIfCatB(reg_request):
  """Separates the conditionals from the registration request, if needed."""
  if reg_request['cbsdCategory'] == 'A':
    return reg_request, None

  conditional_keys = [
      'cbsdCategory', 'fccId', 'cbsdSerialNumber', 'airInterface',
      'installationParam', 'measCapability'
  ]
  reg_conditional_keys = ['airInterface', 'installationParam', 'measCapability']
  conditionals = {key: reg_request[key] for key in conditional_keys}
  reg_request = {
      key: reg_request[key]
      for key in reg_request
      if key not in reg_conditional_keys
  }
  return reg_request, conditionals


def FinalizeRegistrationRequests(reg_requests):
  """Finalizes registration requests.

  Args:
    reg_requests: A list of registration requests.

  Returns:
    A corresponding list of 'conditionals' dict (for each cat B only).
    The input registration_requests are also cleaned appropriately and IDs are
    injected.
  """
  conditionals = []
  for k, reg_request in enumerate(reg_requests):
    reg_request.update({
        'fccId': 'test_fcc_id',
        'userId': 'test_user_id',
        'cbsdSerialNumber': 'test_serial_number_%d' % k,
        'callSign': 'test_callsign',
        'airInterface': {
            'radioTechnology': 'E_UTRA'
        },
        'measCapability': []
    })

    new_reg_request, cond = CreateConditionalsIfCatB(reg_request)
    # Clear and update so that the input is modified.
    reg_request.clear()
    reg_request.update(new_reg_request)
    if cond:
      conditionals.append(cond)
  return conditionals
