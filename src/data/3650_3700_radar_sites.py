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

from lxml import etree
from pykml.factory import KML_ElementMaker as KML
import math
import os

# This script prepares a KML file containing the 80km exclusion zones around
# three 3650-3700 radar sites specified in the FCC's Report and Order 15-47A1.
# The three sites are specified in footnote US109 to the table of frequency
# allocations in 2.106:
#   St. Inigoes, MD (38 10' N,     76 23' W)
#   Pascagoula, MS  (30 22' N,     88 29' W)
#   Pensacola, FL   (30 21' 28" N, 87 16' 26" W)

radar_sites = [
  ['St. Inigoes MD', 38, 10,  0, 'N', 76, 23,  0, 'W'],
  ['Pascagoula MS',  30, 22,  0, 'N', 88, 29,  0, 'W'],
  ['Pensacola FL',   30, 21, 28, 'N', 87, 16, 26, 'W']
]

# This is the protection zone radius in meters from the center point of
# each site. Equal to 80km.
zone_radius = 80000

# The earth radius in meters.
earth_radius = 6371000

def AddPlacemarkAndZone(doc, site):
  name = site[0]
  lat = float(site[1]) + float(site[2])/60.0 + float(site[3])/3600.0;
  if site[4] == 'S':
    lat = -lat
  lng = float(site[5]) + float(site[6])/60.0 + float(site[7])/3600.0;
  if site[8] == 'W':
    lng = -lng
  print 'Adding placemark for %s at (%f, %f)' % (name, lat, lng)

  pm = KML.Placemark(
    KML.name(name),
    KML.styleUrl('#pm'),
    KML.Point(
      KML.coordinates('%f,%f,0' % (lng, lat))
    )
  )
  doc.append(pm)

  zone = KML.Placemark(
    KML.name('%s zone' % name),
    KML.styleUrl('#ts'),
    KML.Polygon(
      KML.extrude(0),
      KML.altitudeMode('clampToGround')
    )
  )
  poly = zone.Polygon

  d = float(zone_radius) / float(earth_radius)
  coords = []
  for az in range(0, 359):
    a = float(az)
    print 'At az %f d=%f from (%f, %f)' % (float(az), d, lat, lng)
    lat2 = math.asin(math.sin(math.radians(lat))*math.cos(d) +
                     math.cos(math.radians(lat))*math.sin(d)*math.cos(math.radians(a)))
    lng2 = math.radians(lng) + math.atan2(
               math.sin(math.radians(a))*math.sin(d)*math.cos(math.radians(lat)),
               math.cos(d) - math.sin(math.radians(lat))*math.sin(lat2))
    print 'Got %f %f' % (math.degrees(lat2), math.degrees(lng2))
    coords.append([math.degrees(lng2), math.degrees(lat2)])
  coords.append(coords[0])
  latlngCoords = []
  for c in coords:
    latlngCoords.append('%f,%f,0' % (c[0], c[1]))
  coordinates = ' '.join(latlngCoords)
  poly.append(KML.outerBoundaryIs(
    KML.LinearRing(
      KML.coordinates(coordinates)
    )
  ))
  doc.append(zone)


# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
fccDir = os.path.join(os.path.join(rootDir, 'data'), 'fcc')

doc = KML.kml(
  KML.Document(
    KML.name('3650-3700 Radar Sites'),
    KML.Style(
      KML.LineStyle(
        KML.color('ff00ff00'),
        KML.width(2)
      ),
      KML.PolyStyle(
        KML.color('66006600')
      ),
      id="ts"
    ),
    KML.Style(
      KML.color('ff00ff00'),
      id="pm"
    )
  )
)

AddPlacemarkAndZone(doc.Document, radar_sites[0])
AddPlacemarkAndZone(doc.Document, radar_sites[1])
AddPlacemarkAndZone(doc.Document, radar_sites[2])

kmlFilename = os.path.join(fccDir, '3650_3700_radar_sites.kml')
print 'Writing output file %s' % kmlFilename
out = open(kmlFilename, 'w')
out.write(etree.tostring(doc, pretty_print=True))
out.close()

