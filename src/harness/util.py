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
import geojson
import random
from datetime import datetime

def winnforum_testcase(testcase):
  """Decorator for common features(such as logging) for Winnforum test cases."""

  def decorated_testcase(*args, **kwargs):
    logging.info('Running Winnforum test case %s:', testcase.__name__)
    logging.info(testcase.__doc__)
    testcase(*args, **kwargs)

  return decorated_testcase


def _getRandomLatLongInPolygon(polygon):
  
  try:
    geojson_ppa = geojson.loads(json.dumps(polygon['features'][0]['geometry']))
    ppa_polygon = shape(geojson_ppa)
    min_lng, min_lat, max_lng, max_lat = ppa_polygon.bounds
    lng = random.uniform(min_lng, max_lng)
    lng_line = LineString([(lng, min_lat), (lng, max_lat)])
    lng_line_intercept_min, lng_line_intercept_max = \
      lng_line.intersection(ppa_polygon).xy[1].tolist()
    lat = random.uniform(lng_line_intercept_min, lng_line_intercept_max)
    if Point([lng, lat]).within(ppa_polygon):
      return lat, lng
    else:
      return _getRandomLatLongInPolygon(polygon)
  except NotImplementedError:
    # If there's no intercept again call the function
    return _getRandomLatLongInPolygon(polygon)


def _changeDateInPpaAndPal(record, prev_date, next_date):
  for key, value in record.iteritems():
    if type(record[key]) is dict:
      _changeDateInPpaAndPal(record[key], prev_date, next_date)
    record[key] = (next_date if 'Expiration' in key else
                  prev_date if 'Date' in key else record[key])
  return record


def makePpaAndPalRecordsConsistent(ppa_record, pal_records,
                                   ppa_fips_code, ppa_census_year,
                                   low_frequency, high_frequency, device):
  """Make PPA, PAL and Device object consistent with the inputs and position 
  the device in the PPA Polygon at some random location

    Args:
      ppa_record: (dictionary) An object containing PPA Record.
      pal_records: (list) A list of PAL Records which has to be
        associated with the PPA.
      ppa_fips_code: (number) The FIPS Code of the Census Tract where 
      the PPA belongs.
      ppa_census_year: (number) The census year in which the census 
      tract was defined.
      low_frequency: (number) The Primary Low Frequency for PAL
      high_frequency: (number) The Primary High Frequency for PAL
      device: (dictionary) An object containing device which has to be
      moved into the PPA Polygon.
    Returns:
      A tuple consisting of PPA Record, PAL Record List and Device with 
      modified Latitude and Longitude
  """

  previous_year_date = datetime.now().replace(year=datetime.now().year - 1)
  next_year_date = datetime.now().replace(year=datetime.now().year + 1)

  for pal_record in pal_records:
    # Change the FIPS Code and Registration Date-Year in Pal Id
    pal_record['palId'] = '/'.join([str(ppa_fips_code) if index == 2 else
                           '%s-%d' % ('{:02d}'.format(previous_year_date.month),
                                      previous_year_date.year)
                           if index == 1 else str(val) for index, val in
                                    enumerate(pal_record['palId'].split('/'))])
    pal_record['userId'] = device['userId']
    # Make the date consistent in Pal Record for Registration and License
    pal_record = _changeDateInPpaAndPal(pal_record,
                                        previous_year_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                        next_year_date.strftime('%Y-%m-%dT%H:%M:%SZ'))
    # Change License Information in Pal
    pal_record['license']['licenseAreaIdentifier'] = str(ppa_fips_code)
    pal_record['license']['licenseAreaExtent'] = \
      'zone/census_tract/census/%d/%d' % (ppa_census_year, ppa_fips_code)
    # Change Frequency Information in Pal
    for assign in ('primaryAssignment', 'secondaryAssignment'):
      pal_record['channelAssignment'][assign]['lowFrequency'] = low_frequency
      pal_record['channelAssignment'][assign]['highFrequency'] = high_frequency
  # Make the date consistent in Ppa Record
  ppa_record = _changeDateInPpaAndPal(ppa_record,
                                      previous_year_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                      next_year_date.strftime('%Y-%m-%dT%H:%M:%SZ'))
  # Add Pal Ids into the Ppa Record
  ppa_record['ppaInfo']['palId'] = [pal_record['palId'] for pal_record
                                    in pal_records]
  device['installationParam']['latitude'], device['installationParam']['longitude'] = \
    _getRandomLatLongInPolygon(ppa_record['zone'])

  return ppa_record, pal_records, device

