This directory contains raw and processed data files from the FCC
defining certain aspects of the 3.5GHz band operation context. 
Copyright on data files is by their creators.

## FCC field offices

* fcc_field_office_locations.csv
   
    This is a simple CSV file listing the FCC field offices and their location. The file
    has 3 columns respectively for the name, latitude and longitude.

## US-Canada border

The US-Canada border is represented by the `uscabdry_resampled.kml` file that is built 
from a process described in the `Winnforum/Common-Data` repository. 
It is the same file as `uscabdry.kml` with new vertices injected along the border so that
the distance between 2 consecutive vertices do not exceed 200m.

Using this resampling in test harness allows for deterministically finding the closest 
point on the border, by selecting the closest vertex.


## US general border

The US general border is described by the `usborder.kml` KML file that is built from a 
process described in the `Winnforum/Common-Data` repository.

It contains polygons representing the assignment authority of the SAS as described 
by the borders in FCC and NTIA source files. The borders represent the territorial 
sea boundary of US jurisdiction as modified by international sea borders reflected
in the NOAA files, and modified by FCC border definitions for US-CA and US-MEX, as
defined by the `us_mex_boundary.kmz` and `uscabdry_resampled.kml` files.
