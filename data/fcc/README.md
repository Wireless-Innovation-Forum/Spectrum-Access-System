This directory contains raw and processed data files from the FCC
defining certain aspects of the 3.5GHz band operation context. 
Copyright on data files is by their creators.

## FCC field offices

* fcc_field_office_locations.csv
   
    This is a simple CSV file listing the FCC field offices and their location. The file
    has 3 columns respectively for the name, latitude and longitude.

## US-Canada border

The US-Canada border is represented by a KML file having gone through the following workflow.

* uscabdry.zip

    This is the raw zip file containing the FCC definition of the US-Canada
    border. It is linked from this page:
    https://www.fcc.gov/encyclopedia/white-space-database-administration-q-page
    and can be retrieved here:
    https://transition.fcc.gov/oet/info/maps/uscabdry/uscabdry.zip

* uscabdry.kmz

    This is a KMZ file with an exact representation of the boundary lines contained
    in the uscabdry.zip file. There are 17 line segments composing this
    boundary, each taken from a separate .MAP file in the uscabdry.zip file.

* uscabdry.kml
    
    This is a KML file produced by the script in `src/data/uscabdry.py`. 
    It contains the US-CA border as processed from the source file by that script, which does
    data reduction, normalization, and some noise removal.

* uscabdry_resampled.kml

    This is a KML file produced by the script in `src/data/resample_uscabdry.py`.
    It is the same file as `uscabdry.kml` with new vertices injected along the border so that 
    the distance between 2 consecutive vertices do not exceed 200m.
    Using this resampling in test harness allows for deterministically finding the
    closest point on the border, by selecting the closest vertex.

## US-Mexican border

The US-Canada border is represented by a KML file having gone through the following workflow.

* us_mex_boundary.zip

    This is the raw zip file containing the FCC definition of the US-Mexico
    border. It is linked from this page:
    https://www.fcc.gov/encyclopedia/white-space-database-administration-q-page
    and can be retrieved here:
    http://www.ibwc.gov/GIS_Maps/downloads/us_mex_boundary.zip

* us_mex_boundary.kmz

    This is a KMZ file with an exact representation of the boundary line
    contained in the `us_mex_boundary.zip` Shapefile.

## US general border

The US general border is described by the `usborder.kml` KML file, 
which is produced by the script in `src/data/usborder.py`. 

It contains polygons representing the assignment authority of the SAS as described 
by the borders in FCC and NTIA source files. The borders represent the territorial 
sea boundary of US jurisdiction as modified by international sea borders reflected
in the NOAA files, and modified by FCC border definitions for US-CA and US-MEX, as
defined by the `us_mex_boundary` and `uscabdry_resampled.kml` files.


