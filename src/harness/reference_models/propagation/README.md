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
  - USGS 3DEP DEM terrain altitude: in data/geo/ned/
  - NLCD land cover: in data/geo/nlcd/

Since the DEM and NLCD data is stored in another repository, you can use soft links.

### Other Location

If not using these location, you should modify the geo/CONFIG.py file to specify
the absolute path to your folders holding these database.
For the NED terrain, one can also directly set the proper terrain directory,
using the routines:

```python
    from reference_models.geo import drive
    drive.ConfigureTerrainDriver(terrain_dir)
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

### Compilation in Linux

To compile these extension modules, you can use the provided top level makefile.
Simply type the following command in a shell:

    `make all`

### Compilation in Windows

The easiest way is to to use the MinGW GCC port for Windows.

#### Using gcc provided by MinGW32

Download and install MingW32 from http://www.mingw.org:

 - The download section of this page will redirect you to SourceForge where you can
 download the MinGW installer: `mingw-get-setup.exe`

 - Run the installer and select both the *mingw32-base* and *mingw32-gcc-g++* packages.
 Optionally you can also select the *mingw-developer-toolkit* package to be able to use makefiles.
 
 - After making selections, proceed with installation by choosing Installation->Update Catalog->Review Changes->Apply

 - By default the MinGW will be installed in `C:/MinGW/`.

Configuration:

 - Open a command prompt and make sure the directory `C:/MinGW/bin` is in the Windows path, by typing: `PATH`
 
 - If not, add it either:
 
   + in the global path settings, under Control Panel => System => Advanced System Settings => Environment Variables
   + or directly in your working command prompt, as the leading directory:
     `set PATH=C:/MinGW/bin;%PATH%`
 
 - If the developer-toolkit package has been installed, you should now be able able to use *make* in the reference_models/propagation directory, as is done for linux. If any issue, you might need to specify the compiler (see below).
 
 - If the developer-toolkit package has not been selected, then you will need to manually call the python distutils commmand on each of the itm/ and ehata/ subdirectories:

```
     python setup.py build_ext --inplace --compiler=mingw32
```
   
   The *--compiler* option may be unnecessary if there is no conflict with other compilers in your system.
   
If during this process, you experience some issues with wrong compiler, or compilation errors, create the file `distutils.cfg` in your PYTHONPATH\Lib\distutils\ directory, holding the following content:

```
    [build]
    compiler=mingw32
```

In case you are using a 64bit version of Python, the previous steps shall be moified to install and use the MinGW 64 bits instead, and compiler directives `compiler=mingw64`

#### Using Microsoft VCC compiler

The configuration steps should be similar to the MinGW, except that the compiler directive to be used (if necessary) is `--compiler=msvc`.

If issue with vcvarsall.bat not being found, try to set the following variables in your command terminal:

```
    set MSSDK=1 
    set DISTUTILS_USE_SDK=1
```
