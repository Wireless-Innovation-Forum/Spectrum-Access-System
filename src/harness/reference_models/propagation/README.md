# The WinnForum R2-SGN-04 Propagation Model Reference Implementation

This directory holds the reference implementation of the WinnForum propagation
models to be used with SAS. This implementation is in Python, and uses the
core propagation model engine (in C++) exposed as python extension.

## Main interface

The two main propagation models provided are accessed through routines:

  - `wf_itm.CalcItmPropagationLoss()`: the ITM propagation model
  - `wf_hybrid.CalcHybridPropagationLoss()`: the hybrid ITM/eHata propagation model

See the corresponding docstrings for full description.

## Geo-Data setup

Before use of the models, one should make sure that the required geodata is
correctly set in the WinnForum/data/ folder for:

  - ITU climate and refractivity files (TropClim.txt and n050.txt): in data/itu
  - USGS 3DEP terrain altitude: in data/ned/
  - NLCD land cover: in data/nlcd/

### Other Location

If not using these location, you should modify the geo/CONFIG.py file to specify
the absolute path to your folders holding these database.
For the NED terrain, one can also directly set the proper terrain directory,
using the routines:

  - `wf_itm.ConfigureTerrainDriver(terrain_dir)`
  - `wf_hybrid.ConfigureTerrainDriver(terrain_dir)`

### NLCD data

The NLCD land cover data is not directly used by the propagation models, but
a region type (among RURAL, SUBURBAN or URBAN) is a required input for the
hybrid propagation model.

To access this region type, use the geo/nlcd.py module which provides two
methods:

 - `GetRegionType(GetLandCoverCodes(lat, lon))`: retrieves the region type for a given lat,lon point
 - `RegionNlcdVote(points)`: retrieves the region type for an area defined by a
 list of points.

### Data caching

For efficiency the terrain and NLCD drivers maintain a small tile cache in LRU fashion.
Each tile covers a 1x1 degree area (approximately 100km x 100km).

The cache allows to avoid the performance hit of reloading tiles in memory when 
doing repetitive calls in the same geographical area.
To configure the cache size, use:

  - `wf_itm.ConfigureTerrainDriver(cache_size=4)`
  - `wf_hybrid.ConfigureTerrainDriver(cache_size=4)`

Note that each model uses its own terrain driver, and cache.
The memory use is about 50MB * cache_size.

For the NLCD driver, the cache size can be configured directly as following:

     `nlcd_driver.SetCacheSize(cache_size=8)`

The NLCD driver cache takes about 12MB * cache_size.

## Core implementation version

The models make uses of the core model implementation found in the `itm` and
`ehata` folders.

These implementations are derived from the original ITS C++ source code, with 
minimal modifications when required for the WinnForum extensions.
They are wrapped as python extension modules.

## Thread Safety

The models are not thread-safe. Do *not* try to run several calculations in parallel
(multiprocessing should be fine).
