## Geo modules for WinnForum Propagation

This folders holds the few modules necessary for the Winnforum propagation
models:

 - `terrain.py`: Terrain driver to read altitude profile data
 - `nlcd.py`: National land Cover (NLCD) driver to read the land cover data
 - `refractivity.py` and `tropoclim.py`: Access to the climate and refractivity world values
 - `vincenty.py`: precise methods for deriving geodesic between two points in the earth
 modeled as ellipsoid
 - `utils.py`: utility routines for computing polygon area, gridding a polygon, etc..
 - `county.py`: county driver to read JSON coutnies geometries.
 - `tiles.py`: list of all expected tiles, for proper error management of IO issues
 - `drive.py`: maintains the singleton drivers to all database
 - `zones.py`: provide access to all zone files provided in KML format.
 - `testutils.py`: miscellaneous utility routines for test

The geo databases (NED, NLCD and ITU) default locations are specified in
the CONFIG.py file to point to upper level folders:

 - `data/geo/ned/`: USGS Terrain Elevation database (1'')
 - `data/geo/nlcd/`: National Land cover database (1'').
 - `data/counties/`: All US counties.
 - `data/itu/`: database of climate and refractivity. 
 - `data/ntia/`: miscellaneous zones related to incumbents protection.
 
Modify the CONFIG.py file if using other locations.

You can use the top level `reference_models/test_config.py` script to validate
the integrity of your geo databases and proper setup:

```
    python test_config.py
```
