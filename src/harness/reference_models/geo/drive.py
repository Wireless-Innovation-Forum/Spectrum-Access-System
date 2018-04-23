#    Copyright 2016-2018 SAS Project Authors. All Rights Reserved.
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

"""Defines all the geo drivers singletons.
"""
from reference_models.geo import census_tract
from reference_models.geo import nlcd
from reference_models.geo import refractivity
from reference_models.geo import tropoclim
from reference_models.geo import terrain


# Initialize all drivers singletons:
# - DEM Terrain.
terrain_driver = terrain.TerrainDriver()

# - NLCD Land Cover.
nlcd_driver = nlcd.NlcdDriver()

# - ITU data: Tropo Climate and Refractivity.
climate_driver = tropoclim.ClimateIndexer()
refract_driver = refractivity.RefractivityIndexer()

# - Census data.
census_tract_driver = census_tract.CensusTractDriver()



def ConfigureTerrainDriver(terrain_dir=None, cache_size=None):
  """Configure the NED terrain driver.

  Note that memory usage is about cache_size * 50MB.

  Inputs:
    terrain_dir: if specified, change the terrain directory.
    cache_size:  if specified, change the terrain tile cache size.
  """
  if terrain_dir is not None:
    terrain_driver.SetTerrainDirectory(terrain_dir)
  if cache_size is not None:
    terrain_driver.SetCacheSize(cache_size)


def ConfigureNlcdDriver(nlcd_dir=None, cache_size=None):
  """Configure the NLCD driver.

  Note that the memory usage is about cache_size * 12MB.

  Inputs:
    nlcd_dir: if specified, changes the NLCD Data default directory.
    cache_size:  if specified, change the NLCD tile cache size.
  """
  if nlcd_dir is not None:
    nlcd_driver.SetNlcdDirectory(nlcd_dir)
  if cache_size is not None:
    nlcd_driver.SetCacheSize(cache_size)


def ConfigureItuDrivers(itu_dir=None):
  """Configure the ITU climate and refractivity drivers.
  """
  if itu_dir is not None:
    climate_driver.ConfigureDataFile(itu_dir)
    refract_driver.ConfigureDataFile(itu_dir)


def ConfigureCensusTractDriver(census_tract_dir=None):
  """Configure the Census Tract driver.

  Inputs:
    census_tract_dir: if specified, changes the census tract default directory.
  """
  if census_tract_dir is not None:
    census_tract_driver.SetCensusTractDirectory(census_tract_dir)
