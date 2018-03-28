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


import numpy as np
import os
import unittest
import geojson
import shapely.geometry as sgeo
from shapely import ops

from reference_models.geo import zones

TEST_DIR = os.path.join(os.path.dirname(__file__),'testdata', 'zones')


class TestZones(unittest.TestCase):

  def test_read_exclusion(self):
    z = zones.GetCoastalProtectionZone()
    print z.area

  def test_read_dpa(self):
    z = zones.GetDPAZones()
    print z['east_dpa_5'].area

if __name__ == '__main__':
  unittest.main()
