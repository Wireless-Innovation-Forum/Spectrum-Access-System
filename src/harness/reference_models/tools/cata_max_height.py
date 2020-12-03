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

"""CatA outdoor maximum antenna height utility.

Computes the maximum allowed height for CatA outdoor, since CatA outdoor
shall not use an antenna height of 6m or higher above the HAAT (and should be
registered as CatB in that case).

Usage:
  from reference_models.tools import cata_max_height
  max_height = cata_max_height.GetCatAOutdoorMaxHeight(lat, lon)

The tool can also be called on the command line:
  python cata_max_height.py 45 -73
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from reference_models.geo import drive


def GetCatAOutdoorMaxHeight(lat, lon):
  """Computes the maximum CatA outdoor antenna height for given 'lat, lon'.

  Args:
    lat, lon: The CatA location.

  Returns:
    A tuple of (max_height_agl, max_height_amsl), holding the maximum CatA
    height in AGL (Above Ground Level) and AMSL (Above Mean Sea Level) formats.
  """
  haat, alt = drive.terrain_driver.ComputeNormalizedHaat(lat, lon)
  max_height_agl = 6. - haat
  max_height_amsl = max_height_agl + alt
  return max_height_agl, max_height_amsl


# For running on the command line
if __name__ == '__main__':
  import sys
  if len(sys.argv) < 3 or sys.argv[1].find('h') != -1:
    print('Usage: cata_max_height.py <lat> <lon>')
    sys.exit()
  max_height_agl, max_height_amsl = GetCatAOutdoorMaxHeight(
      float(sys.argv[1]), float(sys.argv[2]))
  print('Maximum CatA Outdoor height:')
  print('    AGL: %.2fm' % max_height_agl)
  print('    AMSL: %.2fm' % max_height_amsl)
  if max_height_agl < 0:
    print('CatA Outdoor not allowed')
