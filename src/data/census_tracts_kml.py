#    Copyright 2015 SAS Project Authors. All Rights Reserved.
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

# This script retrieves and processes tiger/shapefiles from the US Census
# to create KML files with polygons describing the census tracts.
# The polygons are labeled with the GEOID attribute of the census tracts,
# and the ALAND and AWATER attributes are translated to metadata
# attached to the placemark.
# Placemarks each contain a MultiGeometry attribute which has one or more
# Polygon geometries inside it. These Polygons may be complex (with outer
# and inner boundaries). The point order of the polygon boundaries follows
# KML guidelines: outer boundaries are clockwise, inner boundaries are
# counter-clockwise.

from lxml import etree
from pykml.factory import KML_ElementMaker as KML
from shapely.geometry import Polygon as SPolygon
from shapely.geometry import Point as SPoint
import copy
import io
import os
import re
# shapefile is from pyshp
import shapefile
import shapely.geometry.polygon as polygon
import zipfile


# Unzip all the .zip files in the current directory.
def UnzipFiles():
  if os.path.exists('UNZIPPED'):
    return
  files = os.listdir('.')
  for f in files:
    if os.path.isfile(f) and re.match('.*\.zip$', f):
      print('Unzip %s' % f)
      with zipfile.ZipFile(f) as zf:
        zf.extractall()
  with open('UNZIPPED', 'w'):
    os.utime('UNZIPPED', None)


# Convert a shapefile geometry to a KML placemark. The
# placemark will have one or more polygons in it.
# The name will be the GEOID of the shape.
# Note: the rings in a shp file are "clockwise" meaning they
# go clockwise around their interior. Inner rings are
# counter-clockwise. This property is reversed in the resulting
# KML since KML (and shapely) require counter-clockwise rings.
def ConvertShapeToPlacemark(shape, geoid, aland, awater, kml):
  #if len(shape.parts) > 1:
  #  print('----------geoid=%s aland=%s awater=%s' % (geoid, aland, awater))
  if shape.shapeType != 5:
    raise Exception('Unexpected shape type [%d] in file' % shape.shapeType)

  pm = KML.Placemark(
    KML.name('%s' % geoid),
    KML.styleUrl('#ts'),
    KML.ExtendedData(
      KML.Data(
        KML.displayName('ALAND'),
        KML.value(aland),
        name='string'
      ),
      KML.Data(
        KML.displayName('AWATER'),
        KML.value(awater),
        name='string'
      )
    ),
    KML.MultiGeometry(
      KML.Polygon(
        KML.extrude(0),
        KML.altitudeMode('clampToGround')
      )
    )
  )

  # The parentPoly will be used to append rings, and a
  # new Polygon will be appended for multiple rings in
  # a geography.
  parentPoly = pm.MultiGeometry.Polygon

  #if len(shape.parts) > 1:
  #  print('shape has %d parts' % len(shape.parts))
  for i in range(0, len(shape.parts)):
    lo = shape.parts[i]
    hi = len(shape.points)
    if i < len(shape.parts) - 1:
      hi = shape.parts[i + 1]
    #if len(shape.parts) > 1:
    #  print('shape has points in [%d, %d) of %d' % (lo, hi, len(shape.points)))
    if (shape.points[lo][0] != shape.points[hi-1][0] or
        shape.points[lo][1] != shape.points[hi-1][1]):
      raise Exception('Loop endpoints in [%d, %d) do not match' % (lo, hi))
    coords = []
    for j in reversed(range(lo, hi)):
      lng = shape.points[j][0]
      lat = shape.points[j][1]
      coords.append([lng, lat])

    latlngCoords = []
    for c in coords:
      latlngCoords.append('%f,%f,0' % (c[0], c[1]))
    coordinates = ' '.join(latlngCoords)

    # Note: need LinearRing to compute ccw. Need Polygon to compute contains().
    spoly = SPolygon(coords)
    if i == 0:
      parentSpoly = spoly
    ring = polygon.LinearRing(coords)

    # Some sanity checks to make sure all rings are closed, non-empty,
    # and valid.
    if not ring.is_ring:
      raise Exception('Badly formatted non-ring : %s' % geoid)
    if ring.is_empty:
      raise Exception('Empty geometry found: %s' % geoid)
    if not ring.is_valid:
      raise Exception('Invalid ring: %s' % geoid)

    if not ring.is_ccw:
      # This ring is an internal (enclave) ring.
      rring = copy.deepcopy(ring)
      rring.coords = list(rring.coords)[::-1]
      # Shapely contains does not handle point-overlaps. This
      # means that enclaves which touch the containing ring
      # are not handled correctly. To cure this, we check two
      # points.
      if not (parentSpoly.contains(SPoint(rring.coords[0])) or
              parentSpoly.contains(SPoint(rring.coords[1]))):
        print('Out-of-order enclave')
        # print('ring %s does not contain %s' % (parentSpoly, ring))
        # print(ring)
        # print(rring)
        # Note: if this triggers, we will need to store the polys
        # to figure out which one is the enclosing one. Hopefully
        # the census files will not exhibit this, although it is
        # legal strictly according to the shapefule spec.
        raise Exception('Out-of-order enclave')
        coordinates = coordinates + ' 0,0,0'
        parentPoly.append(KML.innerBoundaryIs(
          KML.LinearRing(
            KML.coordinates(coordinates)
          )
        ))
      else:
        # Find the containing poly...
        parentPoly.append(KML.innerBoundaryIs(
         KML.LinearRing(
            KML.coordinates(coordinates)
          )
        ))
    else:
      if i > 0:
        # Set the new parent polygon ring.
        parentSpoly = spoly
        parentPoly = KML.Polygon(
          KML.extrude(0),
          KML.altitudeMode('clampToGround'))
        pm.MultiGeometry.append(parentPoly)
      parentPoly.append(KML.outerBoundaryIs(
        KML.LinearRing(
          KML.coordinates(coordinates)
        )
      ))

  return pm


# Process a given Shapefile into KML. This will add a new
# placemark with the name of the GEOID of the geometries in
# the shapefile, containing one or more polygons in it.
def ProcessShpFile(f, basename, kml):
  print('Processing shp file %s' % basename)
  with zipfile.ZipFile(f) as zf:
    shpfile = io.BytesIO(zf.read(basename + '.shp'))
    dbffile = io.BytesIO(zf.read(basename + '.dbf'))
    shxfile = io.BytesIO(zf.read(basename + '.shx'))

  shpfile = shapefile.Reader(shp=shpfile, shx=shxfile, dbf=dbffile)
  geoidField = -1
  alandField = -1
  awaterField = -1
  for i in range(0, len(shpfile.fields)):
    field = shpfile.fields[i][0]
    if 'GEOID' in field:
      geoidField = i - 1
    elif 'ALAND' in field:
      alandField = i - 1
    elif 'AWATER' in field:
      awaterField = i - 1
  if geoidField == -1 or alandField == -1 or awaterField == -1:
    raise Exception('Could not find GEOID,ALAND,AWATER in fields %s' % shpfile.fields)

  shapes = 0
  print('Converting %d shapes' % shpfile.numRecords)
  for i in range(0, shpfile.numRecords):
    geoid = shpfile.record(i)[geoidField]
    aland = shpfile.record(i)[alandField]
    awater = shpfile.record(i)[awaterField]
    placemark = ConvertShapeToPlacemark(shpfile.shape(i), geoid, aland, awater, kml)
    shapes += 1
    kml.Document.append(placemark)
  print('Converted %d rings' % shapes)
  zf.close()


# Process a .zip file containing shapefile files and
# create a KML file containing all the polygons described.
def TranslateShpFileToKML(file):
  print('Translating file %s' % file)
  basename = os.path.splitext(os.path.basename(file))[0]
  doc = KML.kml(
    KML.Document(
      KML.name('US Census Tracts ' + basename),
      KML.Style(
        KML.LineStyle(
          KML.color('ff00ff00'),
          KML.width(2)
        ),
        KML.PolyStyle(
          KML.color('66006600')
        ),
        id="ts"
      )
    )
  )
  ProcessShpFile(file, basename, doc)

  kmlFilename = os.path.join(os.path.dirname(file), basename + '.kml')
  print('Writing output file %s' % kmlFilename)
  with open(kmlFilename, 'w+') as outputFile:
    outputFile.write(etree.tostring(doc, pretty_print=True).decode())


# Find the shapefile container directory.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dest = os.path.join(os.path.join(rootDir, 'data'), 'census')
print('Converting shapefile files in %s' % dest)

files = os.listdir(dest)
print('Found %d zip files to translate' % len(files))
for f in files:
  if os.path.isfile(dest + '/' + f) and re.match('.*\.zip$', f):
    TranslateShpFileToKML(dest + '/' + f)
