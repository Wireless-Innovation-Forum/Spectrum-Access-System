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

# This script parses the KML files in the FCC and NOAA data directories
# and assembles an outline of US territorial area for which the SAS will
# have assignment authority. This includes area within the territorial
# sea limits, except as modified by the maritime boundaries with these
# segments: 
#   B0075
#   B0053
#   B0021
#   B0072
#   B0020
#   B0103
#   B0018
#   B0081
#   B0051
#   B0082
# There are several territorial sea border segments which are not relevant
# due to the FCC US-CA and US-Mex border:
#   B0008
#   B0011
#   B0102
#   B0084
#   B0053
#   B0051
# In addition there are some territorial border segments which are holes
# within larger areas. These are within the EEZ and so are ignored by this
# algorithm:
#   B0153
#   B0172
#   B0169
#   B0168
#   B0384
# B0174 and B0138 overlap the FCC US-CA border and so are trimmed.
# B0072 and B0103 overlap the FCC US-Mex border and so are trimmed.
# B0018 shares an interior point with the territorial sea boundary
# and so causes problems -- it is trimmed to fit.
# 
# The area is also bordered by the US-CA FCC border and the US-Mexico FCC
# border. Where the boundary segments do not quite meet, a segment is
# interpolated. This occurs only in off-shore areas.
# The result is exported as a set of Placemarks which each contain a
# MultiGeometry containing polygons which jointly define the extent of the
# assignment authority area.
#
# Incongruity note: the polygon around Semisopochnoi island spans the
# anti-meridian. Google Earth does not render such polygons correctly. Also,
# Google Earth does not render large polygons with many vertices, so
# they will not show up in the viewer.

from lxml import etree
from pykml import parser
from pykml.factory import KML_ElementMaker as KML
from shapely.geometry import LinearRing
import copy
import math
import os
import zipfile


# This function reads the filename provided and returns the parsed
# KML content. The file is assumed to be a .kmz file.
def ReadKMZ(filename):
  with zipfile.ZipFile(filename) as kmz_file:
    with kmz_file.open('doc.kml', 'r') as kml_file:
      doc = parser.parse(kml_file).getroot()
      return doc


# This function reads the KML file provided and returns the parsed
# KML content. The file is assumed to be a .kml file.
def ReadKML(filename):
  with open(filename, 'r') as kml_file:
    doc = parser.parse(kml_file).getroot()
    return doc


# This function attempts to combine the coordinate lists into a single
# list of coordinates. It does so by brute force: comparing the first
# and last elements of each list to the other lists, and combining
# the new list to the first neighbor when the values are the same.
def ConsolidateLists(coordinateLists):
  print 'Comparing %d lists...' % len(coordinateLists)
  final = []
  for lst in coordinateLists:
    if lst[0] == lst[-1]:
      print '    --> on RING %s...%s' % (lst[0], lst[-1])
    else:
      print '    --> on %s...%s' % (lst[0], lst[-1])
    if len(final) == 0:
      final.append(lst)
      continue
    found = False
    for f in final:
      #print '%s...%s compare %s...%s' % (f[0], f[-1], lst[0], lst[-1])
      if f[0] == lst[len(lst)-1]:
        print 'Joining new element list %s...%s with %s...%s' % (lst[0], lst[-1], f[0], f[-1])
        lst.extend(f[1:])
        del(f[:])
        f.extend(lst)
        found = True
        print '    = New list = %s...%s' % (f[0], f[-1])
        break
      elif f[len(f)-1] == lst[0]:
        print 'Joining list %s...%s with new element list %s...%s' % (f[0], f[-1], lst[0], lst[-1])
        f.extend(lst[1:])
        print '    = New list = %s...%s' % (f[0], f[-1])
        found = True
        break
      elif f[0] == lst[0]:
        print 'Reverse joining list %s...%s with new element list %s...%s' % (f[0], f[-1], lst[0], lst[-1])
        r = list(reversed(lst))
        r.extend(f[1:])
        del(f[:])
        f.extend(r)
        print '    = New list = %s...%s' % (f[0], f[-1])
        found = True
        break
      elif f[len(f)-1] == lst[len(lst)-1]:
        print 'Reverse joining new list %s...%s with list %s...%s' % (f[0], f[-1], lst[0], lst[-1])
        r = list(reversed(lst))
        f.extend(r[1:])
        found = True
        print '    = New list = %s...%s' % (f[0], f[-1])
        break
    if not found:
      #print '  Appending...'
      final.append(lst)
  print 'Have %d final lists' % len(final)
  return final


def Distance(p0, p1):
  c0 = p0.split(',')
  c1 = p1.split(',')

  c0x = float(c0[0])
  c0y = float(c0[1])
  c1x = float(c1[0])
  c1y = float(c1[1])

  return math.sqrt((c1x-c0x)*(c1x-c0x) + (c1y-c0y)*(c1y-c0y))


# Close any nearly-closed rings by appending the first point to the last point.
def CloseRings(coordinateLists, distance):
  print 'Closing near-closed rings'
  final = []
  for lst in coordinateLists:
    if lst[0] == lst[len(lst)-1]:
      final.append(lst)
      continue

    latlngLst0 = lst[0].split(',')
    latlngLstN = lst[len(lst)-1].split(',')
    if Distance(lst[0], lst[len(lst)-1]) < distance:
      print 'Closing ring %s...%s' % (lst[0], lst[len(lst)-1])
      lst.append(lst[0])
    final.append(lst)
  return final


# This function splices lists whose endpoints are within a fraction of a degree of touching.
def SpliceLists(coordinateLists, threshold):
  print 'Splicing %d lists...' % len(coordinateLists)
  final = []
  n = 0
  for lst in coordinateLists:
    if len(final) == 0:
      final.append(lst)
      continue
    found = False

    # If the list is already a ring, just continue.
    if lst[0] == lst[len(lst)-1]:
      final.append(lst)
      continue

    #print '   on list [%d] %s...%s' % (len(lst), lst[0], lst[len(lst)-1])

    for f in final:
      latlngLst0 = lst[0].split(',')
      latlngLstN = lst[len(lst)-1].split(',')
      latlngF0 = f[0].split(',')
      latlngFN = f[len(f)-1].split(',')

      if (abs(float(latlngLst0[0]) - float(latlngF0[0])) < threshold and
          abs(float(latlngLst0[1]) - float(latlngF0[1])) < threshold and
          latlngLst0[0] == latlngF0[0]):
        print 'EXACT splice found %s...%s' % (f[0], f[-1])
        print '  with             %s...%s' % (lst[0], lst[-1])
        # Strip the last point from the new segment.
        r = list(reversed(f))
        r.extend(lst[1:])
        del(f[:])
        f.extend(r)
        found = True
        break
      elif (abs(float(latlngLstN[0]) - float(latlngFN[0])) < threshold and
          abs(float(latlngLstN[1]) - float(latlngFN[1])) < threshold):
        found = True
        print 'reverse splice     list %s...%s ' % (f[0], f[len(f)-1])
        print '  with new element list %s...%s\n' % (lst[0], lst[len(lst)-1])
        r = list(reversed(lst))
        f.extend(r)
        found = True
        break
      elif (abs(float(latlngLst0[0]) - float(latlngF0[0])) < threshold and
            abs(float(latlngLst0[1]) - float(latlngF0[1])) < threshold):
        print 'splice 0,0 list         %s...%s' % (f[0], f[len(f)-1])
        print '  with new element list %s...%s\n' % (lst[0], lst[len(lst)-1])
        r = list(reversed(lst))
        r.extend(f)
        del(f[:])
        f.extend(r)
        found = True
        break
      elif (abs(float(latlngLstN[0]) - float(latlngF0[0])) < threshold and
            abs(float(latlngLstN[1]) - float(latlngF0[1])) < threshold):
        print 'splice new list  [%d]     %s...%s' % (len(lst), lst[0], lst[len(lst)-1])
        print '  with element list [%d]  %s...%s\n' % (len(f), f[0], f[len(f)-1])
        lst.extend(f)
        del(f[:])
        f.extend(lst)
        print '  new list [%d] = %s...%s' % (len(f), f[0], f[-1])
        found = True
        break
      elif (abs(float(latlngFN[0]) - float(latlngLst0[0])) < threshold and
            abs(float(latlngFN[1]) - float(latlngLst0[1])) < threshold):
        print 'splice list   [%d]   %s...%s' % (len(f), f[0], f[len(f)-1])
        print '  with new element list [%d] %s...%s\n' % (len(lst), lst[0], lst[len(lst)-1])
        f.extend(lst)
        print '  new list [%d] = %s...%s' % (len(f), f[0], f[-1])
        found = True
        break
    n += 1

    if not found:
      final.append(lst)
  print 'Have %d final lists' % len(final)
  return final

# Need a method to close rings?

# This function finds the wanted border segments from the NOAA border definition.
def FindBorderSegments(doc):
  folders = list(doc.Document.Folder)
  coordinates = []
  for f in folders:
    print 'Found folder %s' % f.name.text
    placemarks = list(f.Placemark)
    line = ''
    for p in placemarks:
      if f.name.text == 'Territorial Sea':
        desc = p.description.text
        if (desc.find('B0008') != -1 or
            desc.find('B0011') != -1 or
            desc.find('B0102') != -1 or
            desc.find('B0084') != -1 or
            desc.find('B0153') != -1 or
            desc.find('B0172') != -1 or
            desc.find('B0169') != -1 or
            desc.find('B0384') != -1 or
            desc.find('B0168') != -1):
          continue

        ls = list(p.MultiGeometry.LineString)
        #print 'keep place %s = %s with %d segments' % (p.attrib['id'], p.name.text, len(ls))
        for l in ls:
          line = l.coordinates.text
          points = line.split(' ')
          #print '  seg size %d' % len(points)
          coords = []
          for pt in points:
            if pt is not '':
              c = pt.split(',')
              # Trim outline near AK
              if (desc.find('B0174') != -1 and
                  float(c[0]) > -133.207 and float(c[1]) < 54.646):
                continue
              # Trim outline near ME
              if (desc.find('B0138') != -1 and
                  float(c[0]) > -67.3014 and float(c[1]) > 44.2):
                continue
              # Normalize -180 to 180 to get equivalence and correct segment merging later on.
              if c[0] == '-180' or c[0] == '180':
                c[0] = '180'
              coords.append('%s,%s,0' % (c[0], c[1]))
          coordinates.append(coords)

      if f.name.text.find('Maritime') != -1:
        desc = p.description.text
        if (desc.find('B0075') != -1 or
            desc.find('B0021') != -1 or
            desc.find('B0020') != -1 or
            desc.find('B0018') != -1 or
            desc.find('B0081') != -1 or
            desc.find('B0082') != -1):
          ls = list(p.MultiGeometry.LineString)
          print 'keep place %s = %s with %d segments' % (p.attrib['id'], p.name.text, len(ls))
          for l in ls:
            line = l.coordinates.text
            points = line.split(' ')
            if desc.find('B0018') != -1:
              points = points[2:]
            coords = []
            for pt in points:
              if pt is not '':
                c = pt.split(',')
                coords.append('%s,%s,0' % (c[0], c[1]))
            print '  have segment [%d] %s...%s' % (len(coords), coords[0], coords[-1])
            coordinates.append(coords)

  print 'Found %d segments' % len(coordinates)
  return coordinates 


# Add the border line segments for the US-Mexico and US-CA borders.
def AddBorderSegments(mexicoDoc, canadaDoc, coordinateLists):
  mexicoFolders = list(mexicoDoc.Document.Folder)
  for f in mexicoFolders:
    p = f.Placemark
    if f.name.text == 'US_Mex_Boundary':
      line = p.LineString.coordinates.text
      points = line.split(' ')
      print 'Adding US-Mex boundary size %d' % len(points)
      coords = []
      for pt in points:
        if pt.strip() is not '':
          c = pt.split(',')
          coords.append('%s,%s,0' % (c[0], c[1]))
      coordinateLists.append(coords)

  canadaBorderPlacemarks = list(canadaDoc.Document.Placemark)
  for p in canadaBorderPlacemarks:
    if (p.name.text == 'AK-CA Boundary' or
        p.name.text == 'CONUS-CA Boundary'):
      line = p.LineString.coordinates.text
      points = line.split(' ')
      # Adjustment: the FCC US-CA border extends out into the Atlantic. Clip
      # the border so it is closer to the territorial sea for creating
      # authorization areas.
      if p.name.text == 'CONUS-CA Boundary':
        points = points[3:]
      print 'Adding %s size %d' % (p.name.text, len(points))
      coords = []
      for pt in points:
        if pt is not '':
          c = pt.split(',')
          coords.append('%s,%s,0' % (c[0], c[1]))
      coordinateLists.append(coords)


# Find the data directory
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dataDir = os.path.join(rootDir, 'data')
fccDir = os.path.join(dataDir, 'fcc')
noaaDir = os.path.join(dataDir, 'noaa')
    
noaaDoc = ReadKMZ(os.path.join(noaaDir, 'USMaritimeLimitsAndBoundariesKML.kmz'))
mexicoDoc = ReadKMZ(os.path.join(fccDir, 'us_mex_boundary.kmz'))
canadaDoc = ReadKML(os.path.join(fccDir, 'uscabdry.kml'))

coordinateLists = FindBorderSegments(noaaDoc)
AddBorderSegments(mexicoDoc, canadaDoc, coordinateLists)

print 'Total segments = %d' % len(coordinateLists)

# Note: this deep copy is for debugging purposes: to add the source data
# to the output KML file for comparison to the derived data.
coordx = copy.deepcopy(coordinateLists)

consolidatedStringsA = ConsolidateLists(coordinateLists)
# Run it through again: if we splice one in the middle of two existing
# segments, it won't latch on. Repeat a couple times to get all the
# way done...
consolidatedStringsB = ConsolidateLists(consolidatedStringsA)
consolidatedStringsC = ConsolidateLists(consolidatedStringsB)
consolidatedStrings = ConsolidateLists(consolidatedStringsC)

closedRings = CloseRings(consolidatedStrings, .001)

# Also run splice a few times to catch middle-splices that don't
# catch both ends.
spliceStringsA = SpliceLists(closedRings, .002)
spliceStringsB = SpliceLists(spliceStringsA, .002)

# Note: Google Earth can't display large polygons. Use
# KML Viewer to view output from further steps.
# Google Earth can show the LineString boundaries for
# comparison to the various source data files.
# http://ivanrublev.me/kml/
coordy = copy.deepcopy(spliceStringsB)
print '===================='
shortSplicedStrings = SpliceLists(spliceStringsB, .002)

# At this point the only holes remaining are fairly large ones.
# We will do another splice with a larger margin of error to
# close those gaps.
longSplicedStrings = SpliceLists(shortSplicedStrings, .3)

# One final call to close rings. The two rings that need closed
# have a couple largish gaps, so use a big threshold.
lineStrings = CloseRings(longSplicedStrings, 1)

# Reverse rings if necessary.
for ls in lineStrings:
  if ls[0] != ls[-1]:
    print 'NOT A RING!'
  coords = []
  for c in ls:
    xy = c.split(',')
    coords.append([float(xy[0]), float(xy[1])])
  lr = LinearRing(coords)
  if not lr.is_ccw:
    print 'Reversing non-CCW ring'
    r = list(reversed(ls))
    del(ls[:])
    ls.extend(r)

doc = KML.kml(
  KML.Document(
    KML.name('US Area'),
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

num = 1
for ls in lineStrings:
  print 'Have final poly len=%d' % len(ls)
  geo_name = '%d' % num
  num += 1
  pm = KML.Placemark(
    KML.name('%s' % geo_name),
    KML.styleUrl('#stl'),
    KML.Polygon(
      KML.extrude(1),
      KML.altitudeMode('clampToGround'),
      KML.outerBoundaryIs(
        KML.LinearRing(
          KML.coordinates(' '.join(ls))
        )
      )
    )
  )
  doc.Document.append(pm)

# For debugging: optionally include the paths of the original source data.
#ns = 10000
#for ls in coordx:
#  # print 'x coordinates=[%s ... %s] (%d)' % (ls[0], ls[len(ls)-1], len(ls))
#  pm = KML.Placemark(
#    KML.name('%d' % ns),
#    KML.styleUrl('#stlx'),
#    KML.LineString(
#      KML.extrude(1),
#      KML.altitudeMode('clampToGround'),
#      KML.coordinates(' '.join(ls))
#    )
#  )
#  ns += 1
#  doc.Document.append(pm)

# For debugging: optionally include the joined paths
#ns = 20000
#for ls in coordy:
#  # print 'y coordinates=[%s ... %s] (%d)' % (ls[0], ls[len(ls)-1], len(ls))
#  pm = KML.Placemark(
#    KML.name('%d' % ns),
#    KML.styleUrl('#stly'),
#    KML.LineString(
#      KML.extrude(1),
#      KML.altitudeMode('clampToGround'),
#      KML.coordinates(' '.join(ls))
#    )
#  )
#  ns += 1
#  doc.Document.append(pm)

# For debugging: optionally include the spliced paths
#ns = 30000
#for ls in lineStrings:
#  # print 'z coordinates=[%s ... %s] (%d)' % (ls[0], ls[len(ls)-1], len(ls))
#  pm = KML.Placemark(
#    KML.name('%d' % ns),
#    KML.styleUrl('#stly'),
#    KML.LineString(
#      KML.extrude(1),
#      KML.altitudeMode('clampToGround'),
#      KML.coordinates(' '.join(ls))
#    )
#  )
#  ns += 1
#  doc.Document.append(pm)

outputFile = open(os.path.join(dataDir, 'usborder.kml'), 'w+')
outputFile.write(etree.tostring(doc, pretty_print=True))
outputFile.close()

