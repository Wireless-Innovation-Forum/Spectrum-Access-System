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

# This script parses the KML file in the FCC border definition expressed
# as a series of folders of point/linestring placemarks and translates
# the provided set of placemarks into a LineString definition. This is then
# re-exported as a new KML file. The coordinates used in the translations
# are those provided in the coordinates tags of the placemarks. The combination
# of different folders of placemarks is done by comparing (stringwise) the
# first and last coordinates of the coordinates, and if they are identical,
# splicing the coordinate lists together.

from lxml import etree
from pykml import parser
from pykml.factory import KML_ElementMaker as KML
import copy
import os
import zipfile


# This function reads the filename provided and returns a string with the
# KML content. The file is assumed to be a .kmz file.
def ReadKML(filename):
  with zipfile.ZipFile(filename) as kmz_file:
    with kmz_file.open('doc.kml', 'r') as kml_file:
      doc = parser.parse(kml_file).getroot()
      return doc


# This function converts a parsed XML segment of the input file to a
# list of coordinates. The Z coordinate is stripped. When a LineString
# entry is found, the second point in the LineString is used as the
# coordinate.
# Note: this method is custom-coded to account for a few oddities in
# the source data.
def ConvertSegmentToLineString(seg):
  print 'Converting segment %s' % seg.Folder.name
  placemarks = list(seg.Folder.Placemark)
  print '  Got %d placemarks' % len(placemarks)
  raw_coords = {}
  last_coord = ''
  for pm in placemarks:
    # Find the sequence number: some of the data may be out of sequence.
    data = pm.ExtendedData.SchemaData.SimpleData
    foundSeq = False
    for d in data:
      if d.attrib['name'] == 'Sequence':
        sequence = int(d.text)
        foundSeq = True
        break
    if not foundSeq:
      raise Exception('No sequence number found for placemark')

    # Data problem: In the QBDRY there is a bunch of overlapped data
    # which basically spans up and down the border. It all appears to
    # be concentrated after the 2150 sequence point. Stripping this
    # data causes no missing border segment except an extremely small
    # section which is patched up by drawing a segment there (this
    # discontinuity was present in the overlapped data as well).
    if seg.Folder.name == 'QBDRY' and sequence > 2145:
      continue

    # Data problem: there is a bad point in LBDRY which is just misplaced.
    # Eliminating this point leaves a small discontinuity which the
    # algorithm fills in. The error is very small, however. It is
    # near La Verendrye Provincial Park. The error introduced is about
    # 600 sq. ft and is conservative for protecting Canadian transmitters
    # (it occurs on the US side of the border).
    if seg.Folder.name == 'LBDRY' and sequence == 14590:
      continue

    # There is a large cluster of data errors near Clove Lake in LBDRY.
    # These errors are re-used sequence numbers, mis-ordered points, and
    # out-of-order problems. The problem area is between sequence
    # number 10000 and 10450. This hack moves all subsequent sequence
    # numbers up by 10000. Then when we hit a duplicate, we'll add 5000
    # and fit them into the sequence space between the sections.
    if seg.Folder.name == 'LBDRY' and sequence > 10450:
      sequence += 10000

    # Note: there is a missing border segment in the middle of HBDRY
    # (in placemark sequence 20550 and 20580). This segment is very
    # straight and follows the existing border, and it is just
    # filled in by this algorithm, so this discontinuity is ignored.

    # Note: there is a missing border segment in the middle of IBDRY
    # (in placemark sequence 04800 and 04830). This segment is not
    # quite straight: the existing border has a small kink in it,
    # indicating missing data point(s). This algorithm just fills in
    # the kink, which introduces an error near Saint-Venant-de-Paquette
    # of about 1000 sq. ft. This error is an extension of the Canadian
    # side of the border, so the error is conservative for the protection
    # of any Canadian equipment.

    # If the placemark is a point, record it.
    if pm.find('.//{http://www.opengis.net/kml/2.2}Point'):
      c = pm.Point.coordinates.text.strip()
      latlng = c.split(',')
      coord = '%s,%s,0' % (latlng[0], latlng[1])
      last_coord = c
      if seg.Folder.name == 'QBDRY':
        print '%s coord=%s' % (sequence, latlng)
    # If the placemark is a linestring, record that.
    elif pm.find('.//{http://www.opengis.net/kml/2.2}LineString'):
      c = pm.LineString.coordinates.text.strip()
      latlng = c.split(' ')
      first_coord = latlng[0]
      second_coord = latlng[1]
      if first_coord != last_coord:
        print '!!!! Discontinuity %s and %s' % (first_coord, last_coord)
      latlng = latlng[1].split(',')

      # Observed data problem: sometimes the sequence number is repeated. The LBDRY section
      # has this problem, resulting in a confused part of the sequencing.
      if sequence in raw_coords:
        print 'Re-sequence!'
        # Hack to boost re-used sequence members up to higher values.
        sequence += 5000
        if seg.Folder.name == 'LBDRY' and sequence >= 10000 and sequence < 10500:
          print 'problem %d : %s' % (sequence, c)
        #latlng = c.split(' ')
        #latlng = latlng[0].split(',')
        print 'new %d = latlng=%s' % (sequence, latlng)

      coord = '%s,%s,0' % (latlng[0], latlng[1])
      last_coord = second_coord
    else:
      raise Exception('No Point or LineString in Placemark')
    raw_coords[sequence] = coord

  # Now assemble the coordinates in sequence order.
  coordinates = []
  for c in sorted(raw_coords):
    coordinates.append(raw_coords[c])

  print '%s coordinates=[%s ... %s] (%d)' % (
      seg.Folder.name.text, coordinates[0], coordinates[len(coordinates)-1],
      len(coordinates))
  return coordinates


# This function attempts to combine the coordinate lists into a single
# list of coordinates. It does so by brute force: comparing the first
# and last elements of each list to the other lists, and combining
# them when the values are the same.
def ConsolidateLists(coordinateLists):
  print 'Comparing %d lists...' % len(coordinateLists)
  final = []
  for lst in coordinateLists:
    print 'On list size %d' % len(lst)
    if len(final) == 0:
      final.append(lst)
      continue
    found = False
    for f in final:
      # print '%s : %s compare %s : %s' % (f[0], f[len(f)-1], lst[0], lst[len(lst)-1])
      if f[0] == lst[len(lst)-1]:
        # print 'Joining new element list ...%s with %s...' % (lst[len(lst)-3:], f[0:3])
        lst.extend(f[1:])
        del(f[:])
        f.extend(lst)
        # print 'Now f=%d', len(f)
        found = True
        break
      elif f[len(f)-1] == lst[0]:
        # print 'Joining list ...%s with new element list %s...' % (f[len(f)-3:], lst[0:3])
        f.extend(lst[1:])
        found = True
        break
      elif f[0] == lst[0]:
        # print 'Reverse joining list %s... with new element list %s...' % (f[0:3], lst[0:3])
        r = list(reversed(lst))
        r.extend(f[1:])
        del(f[:])
        f.extend(r)
        found = True
        break
    if not found:
      final.append(lst)
  print 'Have %d final lists' % len(final)
  return final


# This function splices lists whose endpoints are within a fraction of a degree of touching.
def SpliceLists(coordinateLists):
  print 'Splicing %d lists...' % len(coordinateLists)
  final = []
  for lst in coordinateLists:
    print 'On list size %d' % len(lst)
    if len(final) == 0:
      final.append(lst)
      continue
    found = False

    for f in final:
      latlngLst0 = lst[0].split(',')
      latlngLstN = lst[len(lst)-1].split(',')
      latlngF0 = f[0].split(',')
      latlngFN = f[len(f)-1].split(',')

      if (abs(float(latlngLstN[0]) - float(latlngFN[0])) < .002 and
          abs(float(latlngLstN[1]) - float(latlngFN[1])) < .002):
        found = True
        # print 'reverse splice list ...%s with new element list %s' % (f[len(f)-3:], lst[len(lst)-3:])
        r = list(reversed(lst))
        f.extend(r)
      elif (abs(float(latlngLst0[0]) - float(latlngF0[0])) < 2 and
            abs(float(latlngLst0[1]) - float(latlngF0[1])) < 2):
        # print 'splice list %s... with new element list %s...' % (f[len(f)-3:], lst[0:3])
        f.extend(lst)
        found = Truej
        break

    if not found:
      final.append(lst)
  print 'Have %d final lists' % len(final)
  return final


# Find the data directory
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dataDir = os.path.join(os.path.join(rootDir, 'data'), 'fcc')

    
doc = ReadKML(os.path.join(dataDir, 'uscabdry.kmz'))
segments = list(doc.Folder.Document)
coordinateLists = []
for seg in segments:
  lineString = ConvertSegmentToLineString(seg)
  coordinateLists.append(lineString)

# Note: this deep copy is for debugging purposes: to add the source data
# to the output KML file for comparison to the derived data.
coordx = copy.deepcopy(coordinateLists)

consolidatedStrings = ConsolidateLists(coordinateLists)
lineStrings = SpliceLists(consolidatedStrings)


doc = KML.kml(
  KML.Document(
    KML.name('US-Canada Border'),
    KML.Style(
      KML.LineStyle(
        KML.color('ff0000ff'),
        KML.width(5)
      ),
      id="stl"
    ),
    KML.Style(
      KML.LineStyle(
        KML.color('0000ffff'),
        KML.width(15)
      ),
      id="stlx"
    ),
  )
)

for ls in lineStrings:
  print 'coordinates=[%s ... %s] (%d)' % (ls[0], ls[len(ls)-1], len(ls))
  print 'Have latitude %s' % ls[0].split(',')[1]
  if float(ls[0].split(',')[1]) > 50:
    geo_name = 'AK-CA Boundary'
  else:
    geo_name = 'CONUS-CA Boundary'
  pm = KML.Placemark(
    KML.name('%s' % geo_name),
    KML.styleUrl('#stl'),
    KML.LineString(
      KML.extrude(1),
      KML.altitudeMode('clampToGround'),
      KML.coordinates(' '.join(ls))
    )
  )
  doc.Document.append(pm)

# For debugging: optionally include the paths of the original source data.
#ns = 100
#for ls in coordx:
#  print 'x coordinates=[%s ... %s] (%d)' % (ls[0], ls[len(ls)-1], len(ls))
#  pm = KML.Placemark(
#    KML.name('%d' % ns),
#    KML.styleUrl('#stlx'),
#    KML.LineString(
#      KML.extrude(1),
#      KML.altitudeMode('clampToGround'),
#      KML.coordinates(' '.join(ls))
#    )
#  )
#  ns = ns + 1
#  doc.Document.append(pm)

outputFile = open(os.path.join(dataDir, 'uscabdry.kml'), 'w+')
outputFile.write(etree.tostring(doc, pretty_print=True))
outputFile.close()

