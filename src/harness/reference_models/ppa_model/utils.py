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
from util import getRandomLatLongInPolygon
from reference_models.geo.vincenty import GeodesicPoints
from collections import defaultdict
from datetime import datetime
import random
import json
import os
import glob


def great_circle(**kwargs):
  latitude = kwargs.pop('latitude')
  longitude = kwargs.pop('longitude')
  distance = kwargs.pop('distance')  # In Km.
  azimuth = kwargs.pop('azimuth')
  lat, lon, reverse = GeodesicPoints(latitude, longitude, distance, azimuth)
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
  s = np.r_[x[-(window_len / 2):], x, x[0:window_len / 2]]
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
