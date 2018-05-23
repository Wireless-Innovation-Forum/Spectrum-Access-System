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

Interface:
  # Exclusion zones
  GetGbsExclusionZones()
  GetPart90ExclusionZones()

  # DPA zones: E-DPA (Coastal/ESC) and P-DPA (Portal)
  GetCoastalDpaZones()
  GetPortalDpaZones()

  # Coastal protection zone - for catA
  GetCoastalProtectionZone()

  # FCC Office locations
  GetFccOfficeLocations()

  # US-Canada Border
  GetUsCanadaBorder()

  # For simulation purpose: global US border and urban areas
  GetUsBorder()
  GetUrbanAreas()
"""
import logging
import os
import re
import numpy as np
import shapely.geometry as sgeo
import shapely.ops as ops
from pykml import parser
import zipfile

from reference_models.geo import CONFIG


# The reference files.
PROTECTION_ZONE_FILE = 'protection_zones.kml'
EXCLUSION_ZONE_FILE = 'GB_Part90_EZ.kml'
COASTAL_DPA_ZONE_FILE = 'E-DPAs.kml'
PORTAL_DPA_ZONE_FILE = 'P-DPAs.kml'
FCC_FIELD_OFFICES_FILE = 'fcc_field_office_locations.csv'

# The reference files for extra zones.
USBORDER_FILE = 'usborder.kmz'
URBAN_AREAS_FILE = 'Urban_Areas_3601.kmz'
USCANADA_BORDER_FILE = 'uscabdry_sampled.kmz'


# A frequency splitter - used as DPA properties converter.
def _SplitFreqRange(freq_range):
  """Splits a `freq_range` str in a list of numerical (fmin, fmax) tuples."""
  try:
    fmin, fmax = re.split(',|-', freq_range.strip())
    return [(float(fmin), float(fmax))]
  except AttributeError:
    freq_ranges = []
    for one_range in freq_range:
      fmin, fmax = re.split(',|-', one_range.strip())
      freq_ranges.append((float(fmin), float(fmax)))
    return freq_ranges


# The DPA properties to extract from DPA KMLs.
#    (attribute, converter, default)
# * attribute: the KML attribute name to extract
# * converter: a converter function (float, str, ..)
# * default: Value to use if unset. If default=None, the attribute is mandatory,
#     and an exception will be raised if absent.
# Warning: If modifying, update in dpa_mgr.BuildDpa()
# Warning: currently catbNeighborDist read from separate file, while waiting for
#          process finalization.

# For coastal DPAs.
COASTAL_DPA_PROPERTIES = [('freqRangeMHz', _SplitFreqRange, None),
                          ('protectionCritDbmPer10MHz', float, -144),
                          ('refHeightMeters', float, 50),
                          ('antennaBeamwidthDeg', float, 3.),
                          ('minAzimuthDeg', float, 0.),
                          ('maxAzimuthDeg', float, 360.),
                          ('catBNeighborhoodDistanceKm', float, None)]

# For portal DPAs.
PORTAL_DPA_PROPERTIES = [('freqRangeMHz', _SplitFreqRange, None),
                         ('protectionCritDbmPer10MHz', float, None),
                         ('refHeightMeters', float, None),
                         ('antennaBeamwidthDeg', float, None),
                         ('minAzimuthDeg', float, 0),
                         ('maxAzimuthDeg', float, 360),
                         ('catBNeighborhoodDistanceKm', float, None),
                         ('portalOrg', str, None),
                         ('federalOp', bool, None),
                         ('gmfSerialNumber', str, 'None'),
                         ('fccCallSign', str, 'None')]


# One source of data is the the `protection_zones.kml` preprocessed by
# Winnforum (see src/data/), and which holds both the protection zone and
# exclusion zones.
_COASTAL_PROTECTION_ZONES = [
    'West Combined Contour', 'East-Gulf Combined Contour'
]

# Singleton for operational zones.
_coastal_protection_zone = None
_exclusion_zones_gbs = None
_exclusion_zones_p90 = None
_coastal_dpa_zones = None
_coastal_dpa_path = None
_portal_dpa_zones = None
_portal_dpa_path = None
_border_zone = None
_uscanada_border = None

def _SplitCoordinates(coord):
  """Returns lon,lat from 'coord', a KML coordinate string field."""
  lon, lat, _ = coord.strip().split(',')
  return float(lon), float(lat)


def _GetPoint(point):
  """Gets a Point from a placemark."""
  coord = point.coordinates.text.strip()
  return sgeo.Point(_SplitCoordinates(coord))


def _GetPolygon(poly):
  """Returns a |shapely.geometry.Polygon| from a KML 'Polygon' element."""
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


# A private struct for configurable zone with geometry and attributes
class _Zone(object):
  """A simplistic struct holder for zones."""
  def __init__(self, fields):
    """Initializes attributes to None for a list of `fields`."""
    self.fields = fields
    for field in fields:
      setattr(self, field, None)

  def __repr__(self):
    """Return zone representation."""
    return 'Zone(geometry=%s, %s)' % (
        'None' if not hasattr(self, 'geometry') else self.geometry.type,
        ', '.join(['%s=%s' % (attr, getattr(self, attr)) for attr in self.fields]))


def _ReadKmlZones(kml_path, root_id_zone='Placemark', ignore_if_parent=None,
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
    if ignore_if_parent is not None and element.getparent().tag.endswith(ignore_if_parent):
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
                for point in element.findall('.//' + tag + 'Point')]
      geometry = ops.unary_union(points)

    # Read the data_fields
    if data_fields is None:
      zones[name] = geometry
    else:
      zone = _Zone(data_fields)
      zone.geometry = geometry
      data_fields_lower = [field.lower() for field in data_fields]
      zones[name] = zone
      ext_data = element.ExtendedData.getchildren()
      for data in ext_data:
        data_attrib = data.attrib['name']
        data_value = str(data.value)
        if data_attrib.lower() in data_fields_lower:
          if getattr(zone, data_attrib) is None:
            setattr(zone, data_attrib, data_value)
          else:
            existing_data = getattr(zone, data_attrib)
            try:
              existing_data.append(str(data_value))
              setattr(zone, data_attrib, existing_data)
            except:
              setattr(zone, data_attrib, [existing_data, str(data_value)])

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


def _GetAllExclusionZones():
  """Read all exclusion zones."""
  global _exclusion_zones_gbs
  global _exclusion_zones_p90
  if _exclusion_zones_gbs is None:
    kml_file = os.path.join(CONFIG.GetNtiaDir(), EXCLUSION_ZONE_FILE)
    zones = _ReadKmlZones(kml_file, data_fields=['freqRangeMhz'])
    gbs_zones = []
    p90_zones = []
    for name, zone in zones.items():
      freq_range = _SplitFreqRange(zone.freqRangeMhz)
      if (3550, 3650) in freq_range:
        gbs_zones.append(zone.geometry)
      elif (3650, 3700) in freq_range:
        p90_zones.append(zone.geometry)
      else:
        raise ValueError('Zone %s: unsupported freq range %r',
                         name, freq_range)
    _exclusion_zones_gbs = ops.unary_union(gbs_zones)
    _exclusion_zones_p90 = ops.unary_union(p90_zones)


def _CheckDpaValidity(dpa_zones, attributes):
  """Checks that DPA is valid, ie all attributes actually set.

  Raise:
    ValueError: if some attributes unset.
  """
  for name, zone in dpa_zones.items():
    for attr in attributes:
      if getattr(zone, attr) is None:
        raise ValueError('DPA %s: attribute %s is unset' % (name, attr))


def _LoadDpaZones(kml_path, properties):
  """Loads DPA zones from a `kml_path` - See GetCoastalDpaZones for returned format.

  Args:
    kml_path: Path to the DPA KML.
    properties: A list of tuple (kml_attribute, converter) for extracting the DPA KML info:
      * kml_attr: a string defining the data attribute in the KML
      * converter: a converter routine, for example `float`.
  """
  # Manage the case where some items are in a Folder structure instead of Placemark
  dpa_zones = _ReadKmlZones(kml_path, root_id_zone='Placemark',
                            #ignore_if_parent='Folder', # useful if dpa_zones2 below used
                            data_fields=[attr for attr,_,_ in properties])
  # Early version of KML files had some DPA as folder. Support it
  #dpa_zones2 = _ReadKmlZones(kml_path, root_id_zone='Folder',
  #                           data_fields=[attr for attr,_,_ in properties])
  #dpa_zones.update(dpa_zones2)

  # Validity check that all required parameters are set properly
  _CheckDpaValidity(dpa_zones, [attr for attr, _, default in properties
                                if default is None])

  # Now adapt the data with converters and set defaults
  for name, zone in dpa_zones.items():
    for attr, cvt, default in properties:
      value = getattr(zone, attr)
      if value is None:
        setattr(zone, attr, default)
      else:
        setattr(zone, attr, cvt(value))

  # Check on the neighbor distances and set defaults
  # TODO(sbdt): This is temp while final KML are produced.
  # Final code should raise an exception for those which are mandatory by the spec,
  # and use the standard default for the optional ones.
  for name, zone in dpa_zones.items():
    if np.isnan(zone.catBNeighborhoodDistanceKm):
      zone.catBNeighborhoodDistanceKm = 200.

  return dpa_zones


#=============================================================
# Public interface below

def GetCoastalProtectionZone():
  """Returns the coastal protection zone as a |shapely.MultiPolygon|.

  The coastal protection zone is optionally used for DPA CatA neighborhood.
  """
  global _coastal_protection_zone
  if _coastal_protection_zone is None:
    kml_file = os.path.join(CONFIG.GetNtiaDir(), PROTECTION_ZONE_FILE)
    zones = _ReadKmlZones(kml_file)
    _coastal_protection_zone = ops.unary_union([zones[name]
                                                for name in _COASTAL_PROTECTION_ZONES])
  return _coastal_protection_zone


def GetGbsExclusionZones():
  """Returns all GBS exclusion zones as a |shapely.MultiPolygon|.

  The GBS exclusion zone are used for protecting Ground Based Station
  transmitting below 3500MHz.
  """
  _GetAllExclusionZones()
  return _exclusion_zones_gbs


def GetPart90ExclusionZones():
  """Returns all Part90 federal exclusion zones as a |shapely.MultiPolygon|."""
  _GetAllExclusionZones()
  return _exclusion_zones_p90


def GetCoastalDpaZones(kml_path=None):
  """Gets Coastal DPA zones.

  Coastal DPA zones are Dynamic Protection Area monitored through the use of ESC sensors.

  Args:
    kml_path: Optional path to the Coastal DPA KML. If unspecified, use the default one
      from the `data/ntia/` folder.

  Returns:
    A dict of DPA struct keyed by their names, each one holding following attributes:
      geometry: A |shapely.Polygon  or Point| defining the DPA.
      protectionCritDbmPer10MHz: The protection threshold (dBm/10MHz).
      refHeightMeters: The radar antenna height (meters).
      antennaBeamwidthDeg: The antenna beamwidth (degrees).
      minAzimuthDeg: The radar min azimuth (degrees).
      maxAzimuthDeg: The radar max azimuth (degrees).
      catBNeighborDist: The CatB neighboring distance (km).
  """
  global _coastal_dpa_zones
  global _coastal_dpa_path
  if _coastal_dpa_zones is None  or kml_path != _coastal_dpa_path:
    _coastal_dpa_path = kml_path
    if kml_path is None: kml_path = os.path.join(CONFIG.GetNtiaDir(), COASTAL_DPA_ZONE_FILE)
    _coastal_dpa_zones = _LoadDpaZones(kml_path, COASTAL_DPA_PROPERTIES)
  return _coastal_dpa_zones


def GetPortalDpaZones(kml_path=None):
  """Gets Portal DPA zones.

  Portal DPA zones are Dynamic Protection Area monitored through the use of portal.

  Args:
    kml_path: Optional path to the Portal DPA KML. If unspecified, use the default one
      from the `data/ntia/` folder.

  Returns:
    A dict of DPA struct keyed by their names, each one holding following attributes:
      geometry: A |shapely.Polygon or Point| defining the DPA.
      protectionCritDbmPer10MHz: The protection threshold (dBm/10MHz).
      refHeightMeters: The radar antenna height (meters).
      antennaBeamwidthDeg: The antenna beamwidth (degrees).
      minAzimuthDeg: The radar min azimuth (degrees).
      maxAzimuthDeg: The radar max azimuth (degrees).
      catBNeighborDist: The CatB neighboring distance (km).
  """
  global _portal_dpa_zones
  global _portal_dpa_path
  if _portal_dpa_zones is None or kml_path != _portal_dpa_path:
    _portal_dpa_path = kml_path
    if kml_path is None: kml_path = os.path.join(CONFIG.GetNtiaDir(), PORTAL_DPA_ZONE_FILE)
    _portal_dpa_zones = _LoadDpaZones(kml_path, PORTAL_DPA_PROPERTIES)
  return _portal_dpa_zones


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

  Note: Client code should cache it as expensive to load (and not cached here).

  Args:
    simplify_deg: if defined, simplify the zone with given tolerance (degrees).
      Default is 1e-3 which corresponds roughly to 100m in continental US.
  """
  kml_file = os.path.join(CONFIG.GetNtiaDir(), URBAN_AREAS_FILE)
  zones = _ReadKmlZones(kml_file, root_id_zone='Document', simplify=simplify_deg)
  urban_areas = sgeo.GeometryCollection(zones.values())  # ops.unary_union(zones.values())
  return urban_areas


def GetFccOfficeLocations():
  """Gets FCC Office locations.

  14 FCC field offices that require protection are defined.

  Returns:
    A list of locations defined as dict with keys 'latitude' and 'longitude'.
  """
  fcc_file = os.path.join(CONFIG.GetFccDir(), FCC_FIELD_OFFICES_FILE)
  fcc_offices = [{'latitude': lat,
                  'longitude': lng}
                 for lat, lng in np.loadtxt(fcc_file, delimiter=',', usecols=(1, 2))]
  return fcc_offices
