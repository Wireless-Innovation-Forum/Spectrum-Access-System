import json
import os

from reference_models.geo import CONFIG


class CensusTractDriver:
  def __init__(self, census_tract_directory=None, ):
    self.SetCensusTractDirectory(census_tract_directory)

  def SetCensusTractDirectory(self, census_tract_directory):
    """Configures the Census Tracts data directory."""
    self._census_tract_dir = census_tract_directory
    if self._census_tract_dir is None:
      self._census_tract_dir = CONFIG.GetCensusTractsDir()

  def GetCensusTract(self, fips_code):
    fips_code = str(fips_code)
    census_tract_file_path = os.path.join(self._census_tract_dir, "%s.json" % fips_code)
    print census_tract_file_path
    if os.path.exists(census_tract_file_path):
      with open(census_tract_file_path, 'r') as census_tract_file:
        try:
          return json.load(census_tract_file)
        except:
          raise IOError('Error occurred in opening Census Tract File: %s' % census_tract_file.name)
    else:
      raise Exception("Census Tract data not found with FIPS Code: %s" % fips_code)
