# Placeholder for NED/NLCD geo data

The NED and NLCD geo data are provided in the [SAS-Data repository](https://github.com/Wireless-Innovation-Forum/SAS-Data).

## Installation

By default the reference models look for the data in this folder, under the `ned/` and `nlcd/` folder. Once the `SAS-Data` repository is retrieved (see the corresponding [README file](https://github.com/Wireless-Innovation-Forum/SAS-Data/README.md), you have the following options:

 - make a soft link ned/ and nlcd/ pointing to the SAS-Data ned/ and nlcd folder
 - copy the SAS-Data ned/ and nlcd/ folder here
 - change the [CONFIG.py file](https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/blob/master/src/harness/reference_models/geo/CONFIG.py) pointers to point directly to the SAS-Data `ned/` and `nlcd/` folder.

## Special case for "islands" NLCD data

These data were made available in March 2020. To simplify distribution,
they are included directly in this folder (in addition of the SAS-Data
repository).

To make use of them in the software, simply:

 - unzip all zip files in `nlcd_islands/`
 - copy the `nlcd_islands` into your main `nlcd/` folder (ie. the one
 that you defined in the "Installation" section above).
