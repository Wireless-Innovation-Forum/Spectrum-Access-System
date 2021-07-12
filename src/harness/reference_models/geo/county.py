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

"""Driver for access to County data."""
import json
import os
from reference_models.geo import CONFIG

class CountyDriver(object):
  def __init__(self, county_directory=None):
    self.SetCountyDirectory(county_directory)

  def SetCountyDirectory(self, county_directory):
    """Configures the County data directory."""
    self._county_directory = county_directory
    if self._county_directory is None:
      self._county_directory = CONFIG.GetCountyDir()

  def GetCounty(self, fips_code):
    """Returns the county (as a Python object) for the given FIPS code (as a str)."""
    fips_code = str(fips_code)
    county_file_path = os.path.join(self._county_directory, "%s.json" % fips_code)
    if os.path.exists(county_file_path):
      with open(county_file_path, 'r') as county_file:
        try:
          return json.load(county_file)
        except:
          raise IOError('Error occurred in opening County File: %s' % county_file.name)
    else:
      raise Exception("County data not found with FIPS Code: %s" % fips_code)

