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

import numpy as np
from area import area
import geojson
from shapely.geometry import shape
from shapely.ops import cascaded_union
from src.harness.util import getRandomLatLongInPolygon
from collections import defaultdict
from datetime import datetime
import random
import json
import os
import glob


def to_dist_bear_vincenty(**kwargs):
  """Placeholder to Call Vincenty, will be removed when the Vincenty is moved to reference models"""
  pass


def great_circle(**kwargs):
  latitude = kwargs.pop('latitude')
  longitude = kwargs.pop('longitude')
  distance = kwargs.pop('distance') # In Km.
  azimuth = kwargs.pop('azimuth')
  calc = np.vectorize(to_dist_bear_vincenty)
  lat, lon, reverse = calc(latitude, longitude, distance, azimuth)
  return {"latitude": lat, "longitude": lon}


def check_hole(ppa):
  if hasattr(ppa, 'interiors'):
    if ppa.interiors:
      interior_coords = [interior.coords[:] for interior in ppa.interiors]
      polygon = geojson.Polygon(interior_coords)
      area_hole = area(polygon)
      if area_hole < 500000.0:
        return cascaded_union([ppa, shape(polygon)])
  return ppa


def convert_shape(polygon):
  ppa = shape(polygon).buffer(0)
  return ppa


def smooth(x, window_len=15):
  s = np.r_[x[-1:-window_len / 2:-1], x, x[window_len / 2:0:-1]]
  w = np.hamming(window_len)
  y = np.convolve(w / w.sum(), s, mode='valid')
  return y


def convert_to_polygon(contour_union):
  if contour_union.type == 'MultiPolygon':
    ppa_geojson = geojson.FeatureCollection(
      [geojson.Feature(geometry=check_hole(polygon)) for polygon in contour_union])
  else:
    ppa_geojson = geojson.FeatureCollection(
      [geojson.Feature(geometry=check_hole(contour_union))])
  return ppa_geojson


def make_pal_consistent(pal_record, pal_user_id, low_frequency, high_frequency):
  previous_year_date = datetime.now().replace(year=datetime.now().year - 1)
  next_year_date = datetime.now().replace(year=datetime.now().year + 1)
  pal_fips_code = pal_record['fipsCode']
  pal_census_year = pal_record['censusYear']
  del pal_record['fipsCode'], pal_record['censusYear']
  pal_record = defaultdict(lambda: defaultdict(dict), pal_record)
  pal_record['palId'] = '/'.join(['pal', '%s-%d' %
                                  ('{:02d}'.format(previous_year_date.month),
                                   previous_year_date.year),
                                  str(pal_fips_code), '1'])
  pal_record['userId'] = pal_user_id
  # Make the date consistent in Pal Record for Registration and License
  pal_record['registrationInformation']['registrationDate'] = \
    previous_year_date.strftime('%Y-%m-%dT%H:%M:%SZ')

  # Change License Information in Pal
  pal_record['license']['licenseAreaIdentifier'] = str(pal_fips_code)
  pal_record['license']['licenseAreaExtent'] = \
    'zone/census_tract/census/%d/%d' % (pal_census_year, pal_fips_code)
  pal_record['license']['licenseDate'] = previous_year_date.strftime('%Y-%m-%dT%H:%M:%SZ')
  pal_record['license']['licenseExpiration'] = next_year_date.strftime('%Y-%m-%dT%H:%M:%SZ')
  pal_record['license']['licenseFrequencyChannelId'] = '1'
  # Change Frequency Information in Pal
  pal_record['channelAssignment']['primaryAssignment']['lowFrequency'] = low_frequency
  pal_record['channelAssignment']['primaryAssignment']['highFrequency'] = high_frequency
  # Converting from defaultdict to dict
  return json.loads(json.dumps(pal_record))


def load_files(device_filenames, pal_record_filenames,
              pal_user_id, low_frequency, high_frequency):
  pal_records = []
  devices = []

  for pal_record_filename in pal_record_filenames:
    pal_record = json.load(
      open(os.path.join('..', '..', 'testcases', 'testdata', pal_record_filename)))
    pal_record = make_pal_consistent(pal_record, pal_user_id,
                                   low_frequency, high_frequency)
    pal_records.append(pal_record)

  for device_filename in device_filenames:
    device = json.load(
      open(os.path.join('..', '..', 'testcases', 'testdata', device_filename)))
    if device['userId'] == pal_user_id:
      # Randomly Select the Pal Record
      pal_record = random.choice(pal_records)
      # Move the Device into Random Census Tract Location
      census_tracts = get_census_tracts(pal_record['license']['licenseAreaIdentifier'])
      device['installationParam']['latitude'], \
      device['installationParam']['longitude'] = getRandomLatLongInPolygon(census_tracts)
      devices.append(device)

  return devices, pal_records


def get_census_tracts(fips_code):
  for filename in glob.glob(os.path.join('census_tracts', '*.json')):
    census_tract = json.load(
      open(os.path.join(filename)))
    if census_tract['features'][0]['properties']['GEOID'] == fips_code:
      return {'zone': census_tract}
  raise Exception('Incorrect FIPS Code')


def clip_ppa_census_tracts(pal_records, ppa_polygon):
  census_tracts = []
  for pal_record in pal_records:
    census_geometry = get_census_tracts(pal_record['license']
                                      ['licenseAreaIdentifier'])
    census_tracts.append(census_geometry['zone']['features'][0]['geometry'])
  census_tracts = map(convert_shape, census_tracts)
  census_tracts_union = cascaded_union(census_tracts)
  return ppa_polygon.intersection(census_tracts_union)



