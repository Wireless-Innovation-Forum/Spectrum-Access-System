# Data retrieval and processing scripts

This folder holds all scripts used to retrieve and preprocess data used in the
SAS reference implementation.

## Geo Data

The geo data used by propagation models are stored in Git LFS (Large File Storage)
on the [separate SAS-Data WinnForum repository](https://github.com/Wireless-Innovation-Forum/SAS-Data).

### Integration

The process to plug the data into the environment is:
 - Clone that repository.
 - Unzip the files, by using the `extract_geo.py` script provided in that repository.
 - Point your reference models to that repository, within the `reference_models/geo/CONFIG.py` file.

     
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
