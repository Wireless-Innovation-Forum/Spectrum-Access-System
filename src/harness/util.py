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
"""Helper functions for test harness."""

import logging
import json
from shapely.geometry import shape, Point, LineString
from collections import defaultdict
import random
from datetime import datetime
import uuid


def winnforum_testcase(testcase):
  """Decorator for common features(such as logging) for Winnforum test cases."""

  def decorated_testcase(*args, **kwargs):
    logging.info('Running Winnforum test case %s:', testcase.__name__)
    logging.info(testcase.__doc__)
    testcase(*args, **kwargs)

  return decorated_testcase


def getRandomLatLongInPolygon(ppa):
  """Generate the Random Latitude and Longitude inside the PPA Polygon
  Args:
    ppa: (dictionary) A dictionary containing PPA Record.
  Returns:
    A tuple in the form of latitude and longitude which itself is
    a number.
  """

  try:
    ppa_polygon = shape(ppa['zone']['features'][0]['geometry'])
    min_lng, min_lat, max_lng, max_lat = ppa_polygon.bounds
    lng = random.uniform(min_lng, max_lng)
    lng_line = LineString([(lng, min_lat), (lng, max_lat)])
    lng_line_intercept_min, lng_line_intercept_max = \
      lng_line.intersection(ppa_polygon).xy[1].tolist()
    lat = random.uniform(lng_line_intercept_min, lng_line_intercept_max)
    if Point([lng, lat]).within(ppa_polygon):
      return lat, lng
    else:
      return getRandomLatLongInPolygon(ppa)
  except NotImplementedError:
    # Cannot get the intercept call it again
    return getRandomLatLongInPolygon(ppa)


def makePpaAndPalRecordsConsistent(ppa_record, pal_records, low_frequency,
                                   high_frequency, user_id, cbsd_ids, fcc_channel_id='1'):
  """Make PPA and PAL object consistent with the inputs and add cbsd cluster list 
  to PPA object

    Args:
      ppa_record: (dictionary) A dictionary containing PPA Record.
      pal_records: (list) A list of PAL Records in the form of dictionary
      which has to be associated with the PPA.
      low_frequency: (number) The Primary Low Frequency for PAL.
      high_frequency: (number) The Primary High Frequency for PAL.
      user_id: (string) The userId from the CBSD.
      cbsd_ids: (list) A list containing cbsd ids in string format.
      fcc_channel_id: (string) The FCC-supplied frequency channel identifier.
    Returns:
      A tuple containing a ppa record which itself is a dictionary and pal records 
      list which contains individual pal records in the form of dictionary.
    Note: The PPA Dictionary must contain censusYear (number) and fipsCode(number)
  """

  previous_year_date = datetime.now().replace(year=datetime.now().year - 1)
  next_year_date = datetime.now().replace(year=datetime.now().year + 1)
  ppa_fips_code = ppa_record['fipsCode']
  ppa_census_year = ppa_record['censusYear']
  del ppa_record['censusYear'], ppa_record['fipsCode']

  for index, pal_rec in enumerate(pal_records):
    pal_rec = defaultdict(lambda: defaultdict(dict), pal_rec)
    # Change the FIPS Code and Registration Date-Year in Pal Id
    pal_rec['palId'] = '/'.join(['pal', '%s-%d' % ('{:02d}'.format(previous_year_date.month),
                                                   previous_year_date.year), str(ppa_fips_code),
                                 fcc_channel_id])
    pal_rec['userId'] = user_id
    # Make the date consistent in Pal Record for Registration and License
    pal_rec['registrationInformation']['registrationDate'] = \
      previous_year_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Change License Information in Pal
    pal_rec['license']['licenseAreaIdentifier'] = str(ppa_fips_code)
    pal_rec['license']['licenseAreaExtent'] = \
      'zone/census_tract/census/%d/%d' % (ppa_census_year, ppa_fips_code)
    pal_rec['license']['licenseDate'] = previous_year_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    pal_rec['license']['licenseExpiration'] = next_year_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    pal_rec['license']['licenseFrequencyChannelId'] = fcc_channel_id
    # Change Frequency Information in Pal
    pal_rec['channelAssignment']['primaryAssignment']['lowFrequency'] = low_frequency
    pal_rec['channelAssignment']['primaryAssignment']['highFrequency'] = high_frequency
    # Converting from defaultdict to dict
    pal_records[index] = json.loads(json.dumps(pal_rec))
  # Add Pal Ids into the Ppa Record
  ppa_record = defaultdict(lambda: defaultdict(dict), ppa_record)

  ppa_record['ppaInfo']['palId'] = [pal['palId'] for pal in pal_records]
  ppa_record['id'] = 'zone/ppa/%s/%s/%s' % (ppa_record['creator'],
                                            ppa_record['ppaInfo']['palId'][0],
                                            uuid.uuid4().hex)

  ppa_record['ppaInfo']['cbsdReferenceId'] = cbsd_ids

  # Make the date consistent in Ppa Record
  ppa_record['ppaInfo']['ppaBeginDate'] = previous_year_date.strftime('%Y-%m-%dT%H:%M:%SZ')
  ppa_record['ppaInfo']['ppaExpirationDate'] = next_year_date.strftime('%Y-%m-%dT%H:%M:%SZ')
  ppa_record = json.loads(json.dumps(ppa_record))
  return ppa_record, pal_records
