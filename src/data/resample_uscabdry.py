# Copyright 2018 SAS Project Authors. All Rights Reserved.
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

"""Resample US/Canadian border.

This script takes the `uscabdry.kml` file and resample it into a new KML file
  `uscabdry_sampled.kml`
The resampling insures that 2 consecutive vertex points are no more than D meters away.
Using this resampling in test harness allows for deterministically finding the
closest point on the border, by selecting the closest vertex.

The resampling keeps the original vertices, and add new equidistant vertices in between
two points. The standard method is to use great circle sampling (vincenty method) which
corresponds to line of sight in practice, with one exception:
  a large part of the border (between approximatively 95.153W and 123.318W, the border
  has been defined to be at latitude 49 degrees. For those segments the border is linearly
  interpolated instead.

By default: D=200m
"""
import os
from lxml import etree
from pykml.factory import KML_ElementMaker as KML
import numpy as np
import shapely.geometry as sgeo
import zipfile

from reference_models.geo import vincenty
from reference_models.geo import zones

# --- Parameters ---
# The maximum distance between 2 points
step_meters = 200

input_kml = 'uscabdry.kml'
output_kml = 'uscabdry_sampled.kml'


# The resampling routine
def ResampleUsCanadaBorderLineString(ls, step_m):
  """Resamples a |shapely.LineString|.

  This keeps original linestring vertices, and add new vertices in between
  so as 2 vertices are no more than `step` meters, using either:
    - vincenty great circle method
    - linear interpolation for specific latitude of 49 degree

  Args:
    ls: A |shapely.LineString|
    step: The maximum distance between 2 vertices
  """
  vertices = list(zip(*ls.xy))
  step_km = step_m / 1000.
  out_vertices = []
  for vertex0, vertex1 in zip(vertices[0:-1], vertices[1:]):
    dist_km, _, _ = vincenty.GeodesicDistanceBearing(
        vertex0[1], vertex0[0], vertex1[1], vertex1[0])
    if dist_km < step_km:
      out_vertices.append(vertex0)
    else:
      num_points = int(dist_km / step_km) + 2
      if abs(vertex0[1] - 49) < 1e-3 and abs(vertex1[1] - 49) < 1e-3:
        # departing less than 70m from the 49degree north latitude
        lats = np.interp(range(num_points), [0, num_points-1], [vertex0[1], vertex1[1]])
        lons = np.interp(range(num_points), [0, num_points-1], [vertex0[0], vertex1[0]])
      else:
        lats, lons = vincenty.GeodesicSampling(
            vertex0[1], vertex0[0], vertex1[1], vertex1[0], num_points)

      points = list(zip(lats, lons))
      out_vertices.extend([(point[1], point[0]) for point in points[:-1]])

  out_vertices.append(vertex1)  # add the last vertex
  return sgeo.LineString(out_vertices)

# --- Processing ---
print('Resampling US/Canadian border at %dm' % step_meters)
data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        '..', '..', 'data', 'fcc')

# Read input KML as dict of LineString
input_file = os.path.join(data_dir, input_kml)
uscabdry = zones._ReadKmlBorder(input_file)

# Resample the LineStrings
uscabdry_fine = {}
for name, ls in uscabdry.items():
  uscabdry_fine[name] = ResampleUsCanadaBorderLineString(ls, step_meters)
  print('  segment %s: Before %d After %d' % (
      name, len(ls.xy[0]), len(uscabdry_fine[name].xy[0])))


# Build the output KML
doc = KML.kml(
  KML.Document(
    KML.name('US-Canada Border'),
    KML.Style(
      KML.LineStyle(
        KML.color('ffff00ff'),
        KML.width(3)
      ),
      id="stl"
    ),
    KML.Style(
      KML.LineStyle(
        KML.color('00ffff00'),
        KML.width(15)
      ),
      id="stlx"
    ),
  )
)

def FormatLonLat(lon, lat):
  """Format lat/lon like original KML."""
  # This insure exact formatting as original KML. Basically if outputing
  # the original KML, will produce exact same file.
  if abs(lon) >= 100:
    return '%s,%s,0' % (('%.13f' % lon).rstrip('0').rstrip('.'),
                        ('%.14f' % lat).rstrip('0').rstrip('.'))
  else:
    return '%s,%s,0' % (('%.14f' % lon).rstrip('0').rstrip('.'),
                        ('%.14f' % lat).rstrip('0').rstrip('.'))


for name, ls in uscabdry_fine.items():
  lons, lats = ls.xy
  print('%s: coordinates=[(%.5f,%.5f) ... (%.5f,%.5f)] (num=%d)' % (
      name, lons[0], lats[0], lons[-1], lats[-1], len(lons)))

  pm = KML.Placemark(
    KML.name('%s' % name),
    KML.styleUrl('#stl'),
    KML.LineString(
      KML.extrude(1),
      KML.altitudeMode('clampToGround'),
      KML.coordinates(' '.join(['%s' % FormatLonLat(lon, lat)
                                for lon, lat in zip(lons, lats)]))
    )
  )
  doc.Document.append(pm)

# Save the output KML and KMZ
kml_str = etree.tostring(doc, encoding='utf-8', pretty_print=True).decode()
with open(os.path.join(data_dir, output_kml), 'w') as output_file:
  output_file.write(kml_str)

with zipfile.ZipFile(os.path.join(data_dir, output_kml), 'w') as output_file:
  output_file.writestr(output_kml, kml_str)
