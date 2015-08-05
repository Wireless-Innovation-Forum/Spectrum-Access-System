# Copyright 2015 SAS Project Authors. All Rights Reserved.
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

# This script parses the KML files describing the NTIA-defined exclusion
# zones. It normalizes those zones into compact polygons. Coastal zones
# are consolidated into polygons bounded by the US border (territorial sea).
# Internal zones are consolidated into non-overlapping polygons. The
# internal (ground-based) zones may overlap with coastal zones.

from lxml import etree
from pykml import parser
from pykml.factory import KML_ElementMaker as KML
from shapely.geometry import LinearRing as SLinearRing
from shapely.geometry import LineString as SLineString
from shapely.geometry import MultiPolygon as SMultiPolygon
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon
from shapely.ops import cascaded_union
import math
import os

# This function reads the KML file provided and returns the parsed
# KML content. The file is assumed to be a .kml file.
def ReadKML(filename):
  with open(filename, 'r') as kml_file:
    doc = parser.parse(kml_file).getroot()
    return doc


# This method pulls all the inland zones from the passed KML file.
def ExtractInlandZones(doc):
  placemarks = list(doc.Document.Folder.Placemark)
  zones = {}
  for pm in placemarks:
    name = pm.name.text

    # The Pinon Canyon Maneuver Site location appears to be included
    # in error, and looks like the basis for one of the 3km areas of Fort
    # Carson.
    if name == 'Pinon Canyon Maneuver Site':
      continue

    # Naming for Aberdeen Proving Ground has some inconsistencies.
    # Normalize to a single name.
    if name.find('Aberdeen') != -1:
      name = 'Aberdeen Proving Ground Military Reservation'

    # TODO: make a more general KML->Shapely converter or import one
    # from somewhere.
    polygons = list(pm.MultiGeometry.Polygon)
    print 'Found zone %s with %d polygons' % (name, len(polygons))
    for poly in polygons:
      coordinates = poly.outerBoundaryIs.LinearRing.coordinates.text
      coords = coordinates.split(' ')
      latLng = []
      holeLatLngs = []
      for c in coords:
        if c.strip():
          xy = c.strip().split(',')
          latLng.append([float(xy[0]), float(xy[1])])
      if poly.find('{http://www.opengis.net/kml/2.2}innerBoundaryIs'):
        holes = list(poly.innerBoundaryIs)
        for h in holes:
          holeCoordinates = h.LinearRing.coordinates.text
          holeCoords = holeCoordinates.split(' ')
          holeLatLng = []
          for c in holeCoords:
            if c.strip():
              xy = c.strip().split(',')
              holeLatLng.append([float(xy[0]), float(xy[1])])
          holeLatLngs.append(holeLatLng)
      spolygon = SPolygon(latLng, holeLatLngs)
      if not spolygon.is_valid:
        raise Exception('Invalid polygon for %s' % name)
      if not name in zones:
        zones[name] = []
      print 'Got polygon (%f) for %s' % (spolygon.area, name)
      zones[name].append(spolygon)

  return zones


# This method takes the convex hull of the provided multipolygon
# if it is overlapping.
def AttemptCollapse(name, zone):
  overlaps = False
  for i in range(0,len(zone)):
    for j in range(i+1, len(zone)):
      if zone[i].overlaps(zone[j]):
        overlaps = True
        break
    if overlaps:
      break

  if overlaps:
    print 'Found overlapping zone on %s!' % name
    mp = SMultiPolygon(zone)
    collapsed = cascaded_union(mp)
    if type(collapsed) == SPolygon:
      return [collapsed]
    else:
      print 'Got multipolygon len %d' % len(collapsed.geoms)
      return collapsed.geoms
  else:
    print 'Non-overlapping zone on %s (%d)' % (name, len(zone))
    return zone


def GetConusBorder(doc):
  for pm in doc.Document.Placemark:
    coordinates = pm.Polygon.outerBoundaryIs.LinearRing.coordinates.text
    coords = coordinates.split(' ')
    if len(coords) > 60000:
      latLng = []
      for c in coords:
        if c.strip():
          xy = c.strip().split(',')
          latLng.append([float(xy[0]), float(xy[1])])
      return SLinearRing(latLng)


def Distance(p0, p1):
  c0x = p0[0]
  c0y = p0[1]
  c1x = p1[0]
  c1y = p1[1]
  return math.sqrt((c1x-c0x)*(c1x-c0x) + (c1y-c0y)*(c1y-c0y))


# Get the closest point (flat earth approx) to the probe
# point in the ring. This assumes the test point is within
# 1 unit (degree) of the ring.
def FindClosestPoint(ring, point):
  d = 10
  closestIndex = -1
  for p in range(0, len(ring.coords)):
    pt = ring.coords[p]
    if (abs(point[0]-pt[0]) < 1.0 and
        abs(point[1]-pt[1]) < 1.0):
      dist = Distance(point, pt)
      if dist < d:
        d = dist
        closest = pt
        closestIndex = p

  return closestIndex


# Find the data directory
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dataDir = os.path.join(rootDir, 'data')
ntiaDir = os.path.join(dataDir, 'ntia')

borderDoc = ReadKML(os.path.join(dataDir, 'usborder.kml'))
inlandZoneDoc = ReadKML(os.path.join(ntiaDir, 'ground_based_exclusion_zones.kml'))
coastalZoneDoc = ReadKML(os.path.join(ntiaDir, 'shipborne_radar_envelope_exclusion_zones.kml'))

# Normalize the inland zones
zones = ExtractInlandZones(inlandZoneDoc)
for name in zones:
  if len(zones[name]) > 1:
    collapsed = AttemptCollapse(name, zones[name])
    print 'resetting content for %s' % name
    zones[name] = collapsed

conusBorder = GetConusBorder(borderDoc)

# Collect the coastal zones
print '\n'
coastalLines = {}
for pm in list(coastalZoneDoc.Document.Folder.Placemark):
  name = pm.name.text
  line = pm.LineString.coordinates.text
  coords = line.split(' ')
  latLng = []
  for c in coords:
    if c.strip():
      xy = c.strip().split(',')
      latLng.append([float(xy[0]), float(xy[1])])
  print 'Found exclusion zone border %s (%d)' % (name, len(latLng))
  linestring = SLineString(latLng)
  coastalLines[name] = linestring

  ix = linestring.intersection(conusBorder)
  intersections = ix.geoms
  first = intersections[0]
  if type(first) == SLineString:
    first = first.points[0]
  if type(first) == SPoint:
    first = first.coords[0]
  last = intersections[-1]
  if type(last) == SLineString:
    last = last.coords[-1]
  if type(last) == SPoint:
    last = last.coords[0]

  print 'intersections at %s %s' % (first, last)
  f = FindClosestPoint(conusBorder, first)
  l = FindClosestPoint(conusBorder, last)
  print 'Need ring from %d to %d' % (f, l)
  print '  (%f,%f) to (%f,%f)' % (conusBorder.coords[f][0], conusBorder.coords[f][1], conusBorder.coords[l][0], conusBorder.coords[l][1])

  if name == 'East-Gulf Combined Contour':
    borderSegment = conusBorder.coords[l:]
    borderSegment.extend(conusBorder.coords[0:f-1])
    borderSegment.extend(linestring.coords)
    borderSegment.append(borderSegment[-1])
    zones[name] = [SPolygon(borderSegment)]

  if name == 'West Combined Contour':
    borderSegment = conusBorder.coords[f:l+1]
    borderSegment.extend(list(reversed(linestring.coords)))
    borderSegment.append(borderSegment[-1])
    zones[name] = [SPolygon(borderSegment)]

print '\n'

# Create the KML document skeleton
doc = KML.kml(
  KML.Document(
    KML.name('Protection Zones'),
    KML.Style(
      KML.LineStyle(
        KML.color('ff0000ff'),
        KML.width(2)
      ),
      KML.PolyStyle(
        KML.color('66000066')
      ),
      id="stl"
    ),
    KML.Style(
      KML.LineStyle(
        KML.color('ff00ffff'),
        KML.width(4)
      ),
      KML.PolyStyle(
        KML.color('00006666')
      ),
      id="stlx"
    ),
    KML.Style(
      KML.LineStyle(
        KML.color('ff00ff00'),
        KML.width(2)
      ),
      KML.PolyStyle(
        KML.color('00006666')
      ),
      id="stly"
    ),
  )
)

# Create the KML structure for export
for name in zones:
  print 'Exporting %s' % name
  if len(zones[name]) == 1:
    if name == 'Fort Polk Military Reservation':
      continue
    zone = zones[name][0]

    coords = zone.exterior.coords
    exteriorCoords = []
    for c in coords:
      exteriorCoords.append('%s,%s,0' % (c[0], c[1]))
    
    pm = KML.Placemark(
      KML.name(name),
      KML.styleUrl('#stl'),
      KML.MultiGeometry(
        KML.Polygon(
          KML.extrude(1),
          KML.altitudeMode('clampToGround'),
          KML.outerBoundaryIs(
            KML.LinearRing(
              KML.coordinates(' '.join(exteriorCoords))
            )
          )
        )
      )
    )

    if zone.interiors:
      for i in range(0, len(zone.interiors)):
        coords = zone.interiors[i].coords
        interiorCoords = []
        for c in coords:
          interiorCoords.append('%s,%s,0' % (c[0], c[1]))
        pm.MultiGeometry.Polygon.append(KML.innerBoundaryIs(
          KML.LinearRing(
            KML.coordinates(' '.join(interiorCoords))
          )))
  
  elif len(zones[name]) > 1:
    print 'Exporting multigeometry for %s' % name
    pm = KML.Placemark(
      KML.name(name),
      KML.styleUrl('#stl'),
      KML.MultiGeometry(
      )
    )

    for zone in zones[name]:
      coords = zone.exterior.coords
      exteriorCoords = []
      for c in coords:
        exteriorCoords.append('%s,%s,0' % (c[0], c[1]))
      p = KML.Polygon(
        KML.extrude(1),
        KML.altitudeMode('clampToGround'),
        KML.outerBoundaryIs(
          KML.LinearRing(
            KML.coordinates(' '.join(exteriorCoords))
          )
        )
      )
      pm.MultiGeometry.append(p)
      # TODO: make a better shapely->KML transformer and
      # call that. Support interiors. For now, this case
      # doesn't use them so skip it.

  doc.Document.append(pm)


outputFile = open(os.path.join(dataDir, 'protection_zones.kml'), 'w+')
outputFile.write(etree.tostring(doc, pretty_print=True))
outputFile.close()

