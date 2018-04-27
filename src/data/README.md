# Data retrieval and processing scripts

This folder holds all scripts used to retrieve and preprocess data used in the
SAS reference implementation.

## Geo Data for propagation models

The geo data used by propagation models are stored in Git LFS (Large File Storage)
on the [separate SAS-Data WinnForum repository](https://github.com/Wireless-Innovation-Forum/SAS-Data).

### Integration

The process to plug the data into the environment is:

 - Clone the [`SAS-Data`]((https://github.com/Wireless-Innovation-Forum/SAS-Data)
 repository.
 - Unzip the files, by using the `extract_geo.py` script provided in that repository.
 - Point your reference models to that repository, by one of the following options:
   + create soft links for:
      * `data/geo/ned` -> `SAS_Data/ned`
      * `data/geo/nlcd` -> SAS_Data/nlcd`
   + or modify geo pointers in file `reference_models/geo/CONFIG.py`

### Process for creating NED terrain database

Warning: 
> this procedure shall not be run for replicating the official NED database to be
> used by SAS admins, as it would recreate a different snapshot than the official one which
> was created mainly in July 2017. Use the `SAS-Data/ned` one to have the offical one.
>
> Future official update will be done by Winnforum and published in the `SAS-Data` repository.


The NED terrain tiles are provided directly from USGS FTP site in 1x1 degrees tiles.

Tiles are simply retrieved using the two scripts:

  - `retrieve_orig_ned.py`: retrieves all 1 arcsec resolution tiles from USGS FTP site.
    Final tiles are put in a folder `data/geo/ned_out/`
  - `retrieve_alaska_ned_extra.py`: complete the previous set with missing Alaska tiles
    using Alaska 2-arcsec database and a resampling to 1 arcsec. 
    Final tiles are put in a folder `data/geo/ned_out2/'
  - add manually the data in SAS-Data repository
  
Please note that these 2 scripts keep track of the original downloaded data in 
directories `data/geo/orig_ned` and `data/geo/orig_ned2`. Subsequent run of the script
will only download and process new updated tiles.


### Process for recreating NLCD tiles from scratch

The NLCD tiles have been created with the following process:

 - `retrieve_orig_nlcd.py`: retrieve the original NLCD 16GB CONUS geodata
 - unzip the retrieved zipped files.
 - `retile_nlcd.py` : process the original NLCD into 1x1 degrees tiles with grid
   at multiple of 1 arcsecond. 

Note that the retile script requires a complete NED terrain database available, as it
build NLCD tiles only where corresponding NED tile are available.
So this process shall be done after a snapshot of the NED terrain tile is built.
      

## Other Data

**Section to be completed**.
