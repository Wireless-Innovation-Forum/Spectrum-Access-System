## Description

This directory contains raw data files from the US Census
defining outlines of census tracts used in the 2010 decennial census.

* tl_2010_??_tract10.zip

    Zip files containing TIGER/Line shapefiles which define census tract boundaries
    for the 2010 census. These are zipped files whose name references the FIPS code
    of the state in which that particular file's census tracts lie. The files are
    referenced here: https://www.census.gov/geo/maps-data/data/tiger-line.html
    and can be retrieved from this FTP site:
    ftp://ftp2.census.gov/geo/tiger/TIGER2010/TRACT/2010/
    Copyright on data files is by their creators.

These files are retrieved using the `src/data/extract_census_tracts_json.py` script
in retrieve mode:
 
   `python extract_census_tracts_json.py --retrieve`
   
These raw files are then post-process to extract census tracts into individual GeoJSON
files as explained in the [script README description]((https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/src/data/README.md).

The final generated GeoJSON files are provided as part of the 
[SAS-Data repository](https://github.com/Wireless-Innovation-Forum/SAS-Data) in the 
form of GeoJSON files per FIPS code.
