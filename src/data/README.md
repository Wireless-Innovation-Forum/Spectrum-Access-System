# Data retrieval and processing scripts

This folder holds all scripta used to retrieve and preprocess data used in the
SAS reference implementation.

## Geo Data

Note: The geo data used by propagation models are not stored in Git LFS
(Large File Storage) anymore.

To obtain the reference NED terrain data and NLCD Land cover data, one shall
use the following script:

 - `retrieve_geo.py`: retrieve the NED and NLCD zipped tiles from Google Cloud Storage.
 
     
### Process for recreating NLCD tiles from scratch

The NLCD tiles stored in GCS have been created with the following process:

 - `retrieve_orig_nlcd.py`: retrieve the original NLCD 16GB CONUS geodata
 - `retile_nlcd.py` : process the original NLCD into 1x1 degrees tiles with grid
   at multiple of 1 arcsecond.
      
   
