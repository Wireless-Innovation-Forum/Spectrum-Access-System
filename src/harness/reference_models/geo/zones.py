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
 - Exclusion zones for Ground Based stations and Part90 Exclusion Zones
 - Coastal DPAs.
 - Portal DPAs.
 - US/Canadian border.

Plus a few other useful zones for evaluation/simulation purpose:
 - US Border
 - US Urban areas
"""
import os
import numpy as np
import shapely.geometry as sgeo
import shapely.ops as ops
from pykml import parser
import zipfile

from reference_models.geo import CONFIG


# The reference files.
PROTECTION_ZONE_FILE = 'protection_zones.kml'

COASTAL_DPA_ZONE_FILE = 'Coastal_DPAs.kml'
PORTAL_DPA_ZONE_FILE = 'Portal_DPAs.kml'
EXCLUSION_ZONE_FILE = 'GB_Part90_EZ.kml'

#EXCLUSION_ZONE_FILE = 'protection_zones.kml'
#DPA_ZONE_FILE = 'dpas_12-7-2017.kml'

FCC_FIELD_OFFICES_FILE = 'fcc_field_office_locations.csv'

# The reference files for extra zones.
USBORDER_FILE = 'usborder.kmz'
URBAN_AREAS_FILE = 'Urban_Areas_3601.kmz'
USCANADA_BORDER_FILE = 'uscabdry_sampled.kmz'

# One source of data is the the `protection_zones.kml` preprocessed by
# Winnforum (see src/data/), and which holds both the protection zone and
# exclusion zones.
_COASTAL_PROTECTION_ZONES = [
    'West Combined Contour', 'East-Gulf Combined Contour'
]


# Singleton for operational zones.
_coastal_zone = None
_exclusion_zones_gbs = None
_exclusion_zones_p90 = None
_dpa_zones = None
_border_zone = None
_uscanada_border = None


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


def _GetLineString(linestring):
  """Returns a |shapely.geometry.LineString| from a KML 'LineString' element."""
  coords = linestring.coordinates.text.strip().split(' ')
  points = [_SplitCoordinates(coord) for coord in coords]
  return sgeo.LineString(points)


class _Bunch(object):
  """A simplistic struct."""
  def __init__(self, fields):
    """Initializes attributes to None for a list of `fields`."""
    for field in fields:
      setattr(self, field, None)


def _SplitFreqRange(freq_range):
  try:
    fmin, fmax = freq_range.strip().split(',')
    return [(float(fmin), float(fmax))]
  except AttributeError:
    freq_ranges = []
    for one_range in freq_range:
      fmin, fmax = one_range.strip().split(',')
      freq_ranges.append((float(fmin), float(fmax)))
    return freq_ranges


def _ReadKmlZones(kml_path, root_id_zone='Placemark',
                  data_fields=None, simplify=0):
  """Gets all the zones defined in a KML.

  This assumes that each zone is either a bunch of polygons, or a bunch of points.

  Args:
    kml_path: The path name to the exclusion zone KML or KMZ.
    root_id_zone: The root id defininig a zone. Usually it is 'Placemark'.
    data_fields: List of string defining the data fields to extract from the KML
      'ExtendedData'. If None, nothing is extracted.
    simplify: If set, simplifies the resulting polygons.

  Returns:
    A dictionary of elements keyed by their name, with each elements being:
      - if no data_fields requested:  a |shapely| Polygon/MultiPolygon or Point/MultiPoint
      - if data_fields requested:
        a struct with attributes:
          * 'geometry': a |shapely| Polygon/MultiPolygon or Point/MultiPoint
          * the requested data_fields as attributes. The value are string, or None
            if the data fields is unset in the KML. If several identical data_fields are
            found, they are put in a list.
  """
  if kml_path.endswith('kmz'):
    with zipfile.ZipFile(kml_path) as kmz:
      kml_name = [info.filename for info in kmz.infolist()
                  if os.path.splitext(info.filename)[1] == '.kml'][0]
      with kmz.open(kml_name) as kml_file:
        root = parser.parse(kml_file).getroot()
  else:
    with open(kml_path, 'r') as kml_file:
      root = parser.parse(kml_file).getroot()
  tag = root.tag[:root.tag.rfind('}')+1]
  zones = {}
  for element in root.findall('.//' + tag + root_id_zone):
    # Ignore nested root_id within root_id
    if element.find('.//' + tag + root_id_zone) is not None:
      continue
    name = element.name.text

    # Read the zone geometry
    geometry = None
    polygons = [_GetPolygon(poly)
                for poly in element.findall('.//' + tag + 'Polygon')]
    if polygons:
      if len(polygons) == 1:
        polygon = polygons[0]
      else:
        polygon = sgeo.MultiPolygon(polygons)
      # Fix most invalid polygons
      polygon = polygon.buffer(0)
      if simplify:
        polygon.simplify(simplify)
      if not polygon.is_valid:
        # polygon is broken and should be fixed upstream
        raise ValueError('Polygon %s is invalid and cannot be cured.' % name)
      geometry = polygon
    else:
      points = [_GetPoint(point)
                for poly in element.findall('.//' + tag + 'Point')]
      geometry = ops.unary_union(points)

    # Read the data_fields
    if data_fields is None:
      zones[name] = geometry
    else:
      bunch = _Bunch(data_fields)
      bunch.geometry = geometry
      zones[name] = bunch
      ext_data = element.ExtendedData.getchildren()
      for data in ext_data:
        data_attrib = data.attrib['name']
        data_value = str(data.value)
        if data_attrib in data_fields:
          if getattr(bunch, data_attrib) is None:
            setattr(bunch, data_attrib, data_value)
          else:
            existing_data = getattr(bunch, data_attrib)
            try:
              existing_data.append(str(data_value))
              setattr(bunch, data_attrib, existing_data)
            except:
              setattr(bunch, data_attrib, [existing_data, str(data_value)])

  return zones


def _ReadKmlBorder(kml_path, root_id='Placemark'):
  """Gets the border defined in a KML.

  Args:
    kml_path: The path name to the border file KML or KMZ.
    root_id_zone: The root id defininig a zone. Usually it is 'Placemark'.

  Returns:
    A dictionary of |shapely| LineString keyed by their names.
  """
  if kml_path.endswith('kmz'):
    with zipfile.ZipFile(kml_path) as kmz:
      kml_name = [info.filename for info in kmz.infolist()
                  if os.path.splitext(info.filename)[1] == '.kml'][0]
      with kmz.open(kml_name) as kml_file:
        root = parser.parse(kml_file).getroot()
  else:
    with open(kml_path, 'r') as kml_file:
      root = parser.parse(kml_file).getroot()

  tag = root.tag[:root.tag.rfind('}') + 1]
  linetrings_dict = {}
  for element in root.findall('.//' + tag + root_id):
    # Ignore nested root_id within root_id
    if element.find('.//' + tag + root_id) is not None:
      continue
    name = element.name.text
    linestrings = [
        _GetLineString(l)
        for l in element.findall('.//' + tag + 'LineString')
    ]
    if not linestrings:
      continue
    if len(linestrings) == 1:
      linestring = linestrings[0]
    else:
      linestring = sgeo.MultiLineString(linestrings)

    linetrings_dict[name] = linestring

  return linetrings_dict


def GetCoastalProtectionZone():
  """Returns the coastal protection zone as a |shapely.MultiPolygon|.

  The coastal protection zone is used for DPA CatA neighborhood.
  """
  global _coastal_zone
  if _coastal_zone is None:
    kml_file = os.path.join(CONFIG.GetNtiaDir(), PROTECTION_ZONE_FILE)
    zones = _ReadKmlZones(kml_file)
    _coastal_zone = ops.unary_union([zones[name]
                                     for name in _COASTAL_PROTECTION_ZONES])

  return _coastal_zone


def GetGbsExclusionZones():
  """Returns all GBS exclusion zones.

  The GBS exclusion zone are used for protecting Ground Based Station
  transmitting below 3500MHz.
  """
  global _exclusion_zones_gbs
  if _exclusion_zones_gbs is None:
    kml_file = os.path.join(CONFIG.GetNtiaDir(), EXCLUSION_ZONE_FILE)
    zones = _ReadKmlZones(kml_file, data_fields=['freqRangeMhz'])
    _exclusion_zones_gbs = ops.unary_union(
        [zones[name].geometry for name in zones
         if (3550, 3650) in _SplitFreqRange(zones[name].freqRangeMhz)])
  return _exclusion_zones_gbs


def GetPart90ExclusionZones():
  """Returns all Part90 federal exclusion zones.
  """
  import ipdb; ipdb.set_trace()
  global _exclusion_zones_p90
  if _exclusion_zones_p90 is None:
    kml_file = os.path.join(CONFIG.GetNtiaDir(), EXCLUSION_ZONE_FILE)
    zones = _ReadKmlZones(kml_file, data_fields=['freqRangeMhz'])
    _exclusion_zones_p90 = ops.unary_union(
        [zones[name].geometry for name in zones
         if (3650, 3700) in _SplitFreqRange(zones[name].freqRangeMhz)])
  return _exclusion_zones_p90


def GetDpaZones():
  """Returns DPA zones as a dict of DPA |shapely.Polygon| keyed by their names.

  DPA zones a Dynamic Protection Area protected through the use of ESC sensors.
  """
  global _dpa_zones
  if _dpa_zones is None:
    kml_file = os.path.join(CONFIG.GetNtiaDir(), DPA_ZONE_FILE)
    _dpa_zones = _ReadKmlZones(kml_file, root_id_zone='Document')

  return _dpa_zones


def GetUsCanadaBorder():
  """Gets the US/Canada border as a |shapely.MultiLineString|."""
  global _uscanada_border
  if _uscanada_border is None:
    kml_file = os.path.join(CONFIG.GetFccDir(), USCANADA_BORDER_FILE)
    lines = _ReadKmlBorder(kml_file)
    _uscanada_border = ops.unary_union(lines.values())
  return _uscanada_border


def GetUsBorder():
  """Gets the US border as a |shapely.MultiPolygon|.

  This is a composite US border for simulation purposes only.
  """
  global _border_zone
  if _border_zone is None:
    kml_file = os.path.join(CONFIG.GetFccDir(), USBORDER_FILE)
    zones = _ReadKmlZones(kml_file)
    _border_zone = ops.unary_union(zones.values())
  return _border_zone


def GetUrbanAreas(simplify_deg=1e-3):
  """Gets the US urban area as a |shapely.GeometryCollection|.

  Args:
    simplify_deg: if defined, simplify the zone with given tolerance (degrees).
      Default is 1e-3 which corresponds roughly to 100m in continental US.
  """
  kml_file = os.path.join(CONFIG.GetNtiaDir(), URBAN_AREAS_FILE)
  zones = _ReadKmlZones(kml_file, root_id_zone='Document', simplify=simplify_deg)
  urban_areas = sgeo.GeometryCollection(zones.values())  # ops.unary_union(zones.values())
  return urban_areas


def GetFccOfficeLocations():
  """Returns FCC Office location lat/long as a list of dictionaries.

  14 FCC field offices that require protection are defined in the
  fcc_field_office_locations.csv file.
  """
  fcc_file = os.path.join(CONFIG.GetFccDir(), FCC_FIELD_OFFICES_FILE)
  fcc_offices = [{
      'latitude': lat,
      'longitude': lng
  } for lat, lng in np.loadtxt(fcc_file, delimiter=',', usecols=(1, 2))]
  return fcc_offices
