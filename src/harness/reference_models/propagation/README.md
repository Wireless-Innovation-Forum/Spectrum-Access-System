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

The geographic drivers use these databases:

  - ITU climate and refractivity files (`TropoClim.txt` and `n050.txt`):
    `Spectrum-Access-System/data/itu/`.
  - USGS 3DEP DEM terrain altitude: `Common-Data/data/ned/`.
  - NLCD land cover: `Common-Data/data/nlcd/`.

The default Common-Data checkout is a sibling of Spectrum-Access-System. Existing
local `Spectrum-Access-System/data/geo/ned/` and `data/geo/nlcd/` directories take
precedence over that default. Set `CBRS_COMMON_DATA_DIR` to the root of a
Common-Data checkout to explicitly override both NED and NLCD locations.
The drivers read extracted `.flt` and `.int` tiles, so unpack the required
Common-Data archives before running production calculations. ITU, county and zone
data continue to come from the SAS repository.

### Other Location

For separate NED and NLCD directories, configure the drivers directly:

```python
    from reference_models.geo import drive
    drive.ConfigureTerrainDriver(terrain_dir)
    drive.ConfigureNlcdDriver(nlcd_dir)
```

### NLCD data

The NLCD land cover data is not directly used by the propagation models, but
a region type (among RURAL, SUBURBAN or URBAN) is a required input for the
hybrid propagation model.

To access this region type, use the geo/nlcd.py module which provides two
methods:

 - `nlcd.GetRegionType(drive.nlcd_driver.GetLandCoverCodes(lat, lon))`: retrieves the region type
 for a given lat,lon point
 - `drive.nlcd_driver.RegionNlcdVote(points)`: retrieves the region type for an area defined by a
 list of points.

### Data caching

For efficiency the terrain and NLCD drivers maintain a small tile cache in LRU fashion.
Each tile covers a 1x1 degree area (approximately 100km x 100km).

The cache allows to avoid the performance hit of reloading tiles in memory when 
doing repetitive calls in the same geographical area.
To configure the cache size, use:

```python
    from reference_models.geo import drive
    drive.ConfigureTerrainDriver(cache_size=16)
```

Note that each model uses its own terrain driver, and cache.
The memory use is about 50MB * cache_size.

For the NLCD driver, the cache size can be configured as following:

```python
    from reference_models.geo import drive
    drive.ConfigureNlcdDriver(cache_size=16)
```

The NLCD driver cache takes about 12MB * cache_size.

## Thread Safety

The models are *not* thread-safe. Do *not* try to run several calculations in parallel
(multiprocessing is fine though).

## Core models implementation

The models make uses of the core model implementation found in the `itm` and
`ehata` folders.

These implementations are derived from the original ITS C++ source code, with 
minimal modifications when required for the WinnForum extensions or bug fixes.
They are wrapped as python extension modules.

### Compilation on Linux

Python 3.11 through 3.15 is supported, with Python 3.15 selected by default.
The C++ extensions use setuptools from the repository's locked uv environment.
From the Spectrum-Access-System repository root, run:

```sh
uv sync --locked
uv run --locked make -C src/harness/reference_models/propagation PYTHON=python
```

This builds both ITM and eHata in place. Rebuild them after selecting a different
Python version. A C++ compiler and make are required.

### Compilation on Windows

Install C++ build tools compatible with the selected Python interpreter, then
run these commands in PowerShell from the Spectrum-Access-System repository
root. Using an absolute project path ensures that both extensions use the root
uv environment rather than their individual build metadata:

```powershell
uv sync --locked
$sasRoot = (Get-Location).Path
uv run --locked --project "$sasRoot" --directory "$sasRoot/src/harness/reference_models/propagation/itm" python setup.py build_ext --inplace
uv run --locked --project "$sasRoot" --directory "$sasRoot/src/harness/reference_models/propagation/ehata" python setup.py build_ext --inplace
```

These Windows commands have not been validated on Windows; the native build and
test matrix currently run on Linux.

### Validation

From the repository root, run `uv run --locked python run_unit_tests.py` for the
local unit suite. Add `--with-production-data` after extracting the NED/NLCD tiles
to include the six production data integration tests. See the
[reference models README](../README.md) for details.
