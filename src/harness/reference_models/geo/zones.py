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

"""Zone routines.

These routines allows to read the various zones used by SAS:
 - Protection zone for DPA CatA.
 - Exclusion zones for Ground Based stations.
 - Coastal DPAs.

Plus a few other useful zones for evaluation purpose:
 - TBD.
"""
import os
import numpy as np
import shapely.geometry as sgeo
from pykml import parser

from reference_models.geo import CONFIG


# The reference file for Protection Zones and exclusion zones
PROTECTION_ZONE_FILE = 'protection_zones.kml'
EXCLUSION_ZONE_FILE = 'protection_zones.kml'
DPA_ZONE_FILE = 'dpas_12-7-2017.kml'

# The reference file for Exclusion Zones

# One source of data is the the `protection_zones.kml` preprocessed by
# Winnforum (see src/data/), and which holds both the protection zone and
# exclusion zones.
_COASTAL_PROTECTION_ZONES = [
    'West Combined Contour', 'East-Gulf Combined Contour'
]


def _SplitCoordinates(coord):
  """Returns lon,lat from 'coord', a KML coordinate string field."""
  lon, lat, _ = coord.strip().split(',')
  return float(lon), float(lat)


def _GetPolygon(poly):
  """Gets a Polygon from a placemark"""
  out_ring = poly.outerBoundaryIs.LinearRing.coordinates.text.strip().split(' ')
  out_points = [_SplitCoordinates(coord) for coord in out_ring]
  int_points = []
  try:
    for inner_boundary in poly.innerBoundaryIs:
      inner_ring = inner_boundary.LinearRing.coordinates.text.strip().split(' ')
      int_points.append([_SplitCoordinates(coord) for coord in inner_ring])
  except AttributeError:
    pass
  return sgeo.Polygon(out_points, holes=int_points)


def _ReadKmlZones(kml_path, root_id_zone='Placemark'):
  """Gets all the zones defined in a KML.

  Args:
    kml_path: The path name to the exclusion zone KML.
    root_id_zone: The root id defininig a zone. Usually it is 'Placemark'.

  Returns:
    a dictionary of |shapely| Polygon (or MultiPolygon) keyed by their name.
  """
  with open(kml_path, 'r') as kml_file:
    root = parser.parse(kml_file).getroot()
  tag = root.tag[:root.tag.rfind('}')+1]
  zones = {}
  for element in root.findall('.//' + tag + root_id_zone):
    # Ignore nested root_id within root_id
    if element.find('.//' + tag + root_id_zone) is not None:
      continue
    name = element.name.text
    polygons = [_GetPolygon(poly)
                for poly in element.findall('.//' + tag + 'Polygon')]
    if not polygons: continue
    if len(polygons) == 1:
      polygon = polygons[0]
    else:
      polygon = sgeo.MultiPolygon(polygons)
    # Fix most invalid polygons
    polygon = polygon.buffer(0)
    if not polygon.is_valid:
      # polygon is broken and should be fixed upstream
      raise ValueError('Polygon %s is invalid and cannot be cured.' % name)
    zones[name] = polygon

  return zones


def GetCoastalProtectionZone():
  """Gets the coastal protection zone.

  The coastal protection zone is used for DPA CatA neighborhood.

  Returns:
    A |shapely.MultiPolygon| defining the coastal protection zone.
  """
  kml_file = os.path.join(CONFIG.GetNtiaDir(), PROTECTION_ZONE_FILE)
  zones = _ReadKmlZones(kml_file)
  coastal_zone = sgeo.MultiPolygon(zones[name]
                                   for name in _COASTAL_PROTECTION_ZONES)
  return coastal_zone


def GetGBSExclusionZones():
  """Gets the Ground Based Station exclusion zones.

  The GBS exclusion zone are used for protecting Ground Based Station
  transmitting below 3500MHz.

  Returns:
    A |shapely.MultiPolygon| defining all exclusion zones.
  """
  kml_file = os.path.join(CONFIG.GetNtiaDir(), EXCLUSION_ZONE_FILE)
  zones = _ReadKmlZones(kml_file)
  exclusion_zones = sgeo.MultiPolygon(zones[name] for name in zones
                                      if name not in _COASTAL_PROTECTION_ZONES)
  return exclusion_zones


def GetDPAZones():
  """Gets all the DPA zones.

  DPA zones a Dynamic Protection Area protected through the use of ESC sensors.

  Returns:
    A dict of |shapely.Polygon| keyed by their names.
  """
  kml_file = os.path.join(CONFIG.GetNtiaDir(), DPA_ZONE_FILE)
  zones = _ReadKmlZones(kml_file, root_id_zone='Document')
  return zones
