# Data retrieval and processing scripts

This folder holds all scripts used to retrieve and preprocess data used in the
SAS reference implementation.

## Geo Data

Note: The geo data used by propagation models are stored in Git LFS (Large File Storage)
on the [separate SAS-Data WinnForum repository](https://github.com/Wireless-Innovation-Forum/SAS-Data).

This separate repository is integrated in the SAS main repository as a submodule in `data/geo`. If the subfolder geo/ is not present, you can integrate it
with the command:

```
    # Get the actual data into a `geo` submodule
    git submodule update --init
```
See then the `data/geo/README.md` for further instructions.


### Process for extracting the NED and NLCD tiles from the zip storage

Use the provided script: `extract_geo.py`.

     
### Process for recreating NLCD tiles from scratch

The NLCD tiles have been created with the following process:

 - `retrieve_orig_nlcd.py`: retrieve the original NLCD 16GB CONUS geodata
 - `retile_nlcd.py` : process the original NLCD into 1x1 degrees tiles with grid
   at multiple of 1 arcsecond.
      
### Additional scripts

Retrieval of a snapshot of latest tiles from USGS FTP site can be done using
the script `retrieve_orig_ned.py`. They will be put in a folder `ned_orig`.

Warning: this is for convenience only. Such a snapshot shall not be used, as
it would differ from the official data snapshot to be used by SAS providers 
(currently acquired in July 2017).

## Other Data

**Section to be completed**.
