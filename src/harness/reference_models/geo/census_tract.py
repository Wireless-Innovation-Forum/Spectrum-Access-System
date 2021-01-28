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

"""Driver for access to Census tract data."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os

from reference_models.geo import CONFIG

class CensusTractDriver(object):
  def __init__(self, census_tract_directory=None):
    self.SetCensusTractDirectory(census_tract_directory)

  def SetCensusTractDirectory(self, census_tract_directory):
    """Configures the Census Tracts data directory."""
    self._census_tract_dir = census_tract_directory
    if self._census_tract_dir is None:
      self._census_tract_dir = CONFIG.GetCensusTractsDir()

  def GetCensusTract(self, fips_code):
    """Returns the census tract (as a Python object) for the given FIPS code (as a str)."""
    fips_code = str(fips_code)
    census_tract_file_path = os.path.join(self._census_tract_dir, "%s.json" % fips_code)
    if os.path.exists(census_tract_file_path):
      with open(census_tract_file_path, 'r') as census_tract_file:
        try:
          return json.load(census_tract_file)
        except:
          raise IOError('Error occurred in opening Census Tract File: %s' % census_tract_file.name)
    else:
      raise Exception("Census Tract data not found with FIPS Code: %s" % fips_code)
