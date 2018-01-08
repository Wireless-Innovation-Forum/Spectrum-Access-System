This directory contains the retiled data for the USGS NLCD (National Land Cover Data),
retiled in 1x1 degrees tile with grid every 1 arcsecond.

Content for each tile:

 * nlcd_nXXwYYY_ref.[prj,hdr] : geo referencing header files
 * nlcd_nXXwYYY_ref.int : raw data
 * nlcd_nXXwYYY_ref.md5 : MD5 signature used for future update of the tiles

The reference data can be retrieved by using the `src/data/retrieve_geo.py`, and
corresponds to a retiling operation of the original NLCD data snapshot of 2014, using
the set of following (provided) scripts:

 - `retrieve_orig_nlcd.py`: retrieve the original 2014 NLCD data
 - `retile_nlcd.py`: retile the data into 1x1 degrees tiles with grid point at multiple of 1 arcsecond.


The retiled data can be read by the NLCD driver found in `harness/src/reference_models/geo/nlcd.py`,
and displayed in any GIS tool.
