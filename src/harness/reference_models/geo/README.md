## Geo modules for WinnForum Propagation

This folders holds the few modules necessary for the Winnforum propagation
models:

 - terrain.py : Terrain driver to read altitude profile data
 - nlcd.py: National land Cover (NLCD) driver to read the land cover data
 - refractivity.py and tropoclim.py: Access to the climate and refractivity world values
 - vincenty.py: precise methods for deriving geodesic between two points in the earth
 modeled as ellipsoid
 - utils.py: utility routines for computing polygon area, gridding a polygon, etc..
 - census_tract.py: Census tract driver to read JSON census tracts geometries.
 - tiles.py: list of all expected tiles, for proper error management of IO issues
 - drive.py: maintains the singleton drivers to all database
 - zones.py: provide access to all zone files provided in KML format.
 - testutils.py: miscellaneous utility routines for test

The geo databases (NED, NLCD and ITU) default locations are specified in
the CONFIG.py file to point to upper level folders:
 - data/geo/ned/
 - data/geo/nlcd/
 - data/census_tracts/
 - data/itu/ 
 - data/ntia/
 
Modify the CONFIG.py file if using other locations.

You can use the top level `reference_models/test_config.py` script to validate
the integrity of your geo databases and proper setup:

```
    python test_config.py
```
