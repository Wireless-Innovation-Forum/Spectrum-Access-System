This directory contains the retiled data for the USGS NED (National Elevation Data)
in 1x1 degrees tiles with grid every 1 arcsecond.

Content for each tile:

 * floatnXXwYYY_std.[prj,hdr] : geo referencing header files
 * floatnXXwYYY_std.flt : raw data in ArcFloat format.
 * floatnXXwYYY_std.md5 : MD5 signature used for future update of the tiles

An updated version of some of the tiles are provided with the prefix 
`usgs_ned_1_nXXwYYY_gridfloat_std`: this data corresponds to newer data gathering
techniques (primarily LIDAR).

The reference data can be retrieved by using the `src/data/retrieve_geo.py`, and
corresponds to a snapshot of the latest USGS data available from July 2017.

The data is read by the NED terrain driver found in `harness/src/reference_models/geo/terrain.py`,
and in particular is used by the reference propagation models in `harness/src/reference_models/propagation`.

It can be displayed on any GIS tool.

