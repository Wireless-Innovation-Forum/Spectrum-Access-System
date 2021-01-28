#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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

"""Test the reference model configuration.

This script will fail if misconfigured with hopefully some information on how
to fix.
"""
import os
import sys

# Test that python path correctly setup
try:
  from reference_models.geo import vincenty
except ImportError:
  print('FAILURE: python path not correctly setup.\n'
        '  Add the `harness/` directory in your PYTHONPATH.')
  sys.exit()

ext_fail = False
# Test that models are compiled properly
try:
  from reference_models.propagation.itm import itm
except Exception:
  print('FAILURE: ITM model not compiled as an extension module.\n'
        '  Use the `make all` command in propagation directory.')
  ext_fail = True

try:
  from reference_models.propagation.ehata import ehata
except Exception:
  print('FAILURE: E-Hata model not compiled as an extension module.\n'
        '  Use the `make all` command in propagation directory.')
  ext_fail = True

# Load the geo drivers and test if configured properly
geo_fail = False
from reference_models.geo import nlcd
from reference_models.geo import terrain
from reference_models.geo import tiles

terrain_driver = terrain.TerrainDriver()
nlcd_driver = nlcd.NlcdDriver()

try:
  for key in tiles.NED_TILES:
    terrain_driver.GetTile(*key)
    break
except IOError:
  print('FAILURE: NED terrain database cannot be read.\n'
        '  Configure the `harness/reference_models/geo/CONFIG.py` file.\n'
        '  Make sure that the tiles are unzipped with script:\n'
        '    src/data/extract_geo.py')
  geo_fail = True

try:
  for key in tiles.NLCD_TILES:
    nlcd_driver.GetTile(*key)
    break
except IOError:
  print('FAILURE: NLCD Land cover database cannot be read.\n'
        '  Configure the `harness/reference_models/geo/CONFIG.py` file.\n'
        '  Make sure that the tiles are unzipped with script:\n'
        '    src/data/extract_geo.py')
  geo_fail = True

if geo_fail:
  sys.exit()

# Check if all tiles are present
missing_tiles = []
for key in tiles.NED_TILES:
  ilat, ilon = key
  encoding = '%c%02d%c%03d' % (
      'sn'[ilat >= 0], abs(ilat),
      'we'[ilon >= 0], abs(ilon))

  tile_name1 = 'usgs_ned_1_' + encoding + '_gridfloat_std.flt'
  tile_name2 = 'float' + encoding + '_1_std.flt'
  tile_exists = (os.path.isfile(os.path.join(terrain_driver._terrain_dir, tile_name1))
                 or os.path.isfile(os.path.join(terrain_driver._terrain_dir, tile_name2)))
  if not tile_exists:
    missing_tiles.append(key)

if missing_tiles:
  print('FAILURE: Missing NED terrain tiles:\n'
        '  %r' % missing_tiles)
  geo_fail = True

missing_tiles = []
for key in tiles.NLCD_TILES:
  ilat, ilon = key
  encoding = '%c%02d%c%03d' % (
      'sn'[ilat >= 0], abs(ilat),
      'we'[ilon >= 0], abs(ilon))

  tile_name1 = 'nlcd_' + encoding + '_ref.int'
  tile_name2 = 'nlcd_' + encoding + '.int'
  tile_exists = (os.path.isfile(os.path.join(nlcd_driver._nlcd_dir, tile_name1))
                 or os.path.isfile(os.path.join(nlcd_driver._nlcd_dir, tile_name2)))
  if not tile_exists:
    missing_tiles.append(key)

if missing_tiles:
  print('FAILURE: Missing NLCD land cover tiles:\n'
        '  %r' % missing_tiles)
  geo_fail = True

if not geo_fail and not ext_fail:
  print('SUCCESS: everything properly configured.')
else:
  print('FAILURE: see above messages.')
