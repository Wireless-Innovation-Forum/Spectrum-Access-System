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
      

### Retrieval of census_tracts from USGS FTP site

Retrieval of a census tracts of the year 2010 from USGS FTP site can be done using
the script `extract_census_tracts_json.py`. They will be put in a directory `Spectrum-Access-System/data/census`.
Split the census tracts of GeoJSON into individual files in the directory `Spectrum-Access-System/data/census_tracts`.

There are three steps to retrieval of complete census tracts as follows:
  1. Download all original census tract data from the USGS web site. 
    <pre>
    <code>
    <b>(For ex: $ python extract_census_tracts_json.py --retrieve)</b>
    <b>Spectrum-Access-System/data/census</b> will be created and download all the original census tract data into this
    directory
    </pre>
    </code>
  2. Convert the shape file to GeoJSON.
    <pre>
    <code>
    <b>(For ex: $ python extract_census_tracts_json.py --convert)</b>
    <b>Spectrum-Access-System/data/census</b> will be used to convert shape file to GeoJSON file. Converted GeoJSON file
    will dumped into the same directory.
    </pre>
    </code>
  3. Split the GeoJSON file into individual census tract files based on GEOID.
    <pre>
    <code>
    <b>(For ex: $ python extract_census_tracts_json.py --split)</b>
    <b>Spectrum-Access-System/data/census_tracts</b> will be created and considered for dumping the all GeoJSON files 
    that are split individual GeoJSON per GEOID from converted GeoJSON file.
    will dumped into the same directory.
    </pre>
    </code>

#### Usage and Sample Output
   <pre>
   <code>
   <b> $ python extract_census_tracts_json.py -h </b>
   usage: extract_census_tracts_json.py [-h] (--retrieve | --convert | --split)

   optional arguments:
       -h, --help  show this help message and exit
       --retrieve  Download original census tract data from the USGS web site.
       --convert   Convert the shape file to GeoJSON.
       --split     Split census tract files into individual based on FISP code.
   usage: extract_census_tracts_json.py [-h] (--retrieve | --convert | --split)

   optional arguments:
       -h, --help  show this help message and exit
       --retrieve  Download original census tract data from the USGS web site.
       --convert   Convert the shape file to GeoJSON.
       --split     Split census tract files into individual based on FISP code.
   </pre>
   </code>
  
   1. <b> output for --convert option </b>
   <pre>
   <code>
   <b> $ python extract_census_tracts_json.py --convert </b>
       Namespace(convert=True, retrieve=False, split=False)
       All census tracts will be converted into GeoJSON and placed in directory:<b>/home/cbrsdev/WINNF-GitHub/Spectrum-Access-System/data/census_test</b>
       Convert the ShapelyFile to GeoJson format
       Found 7 zip files to translate
       Processing shp file tl_2010_02_tract10
       ['tl_2010_02_tract10.shp']
    
   <b>tl_2010_02_tract10.shp was converted to tl_2010_02_tract10.json.</b>
   </pre>
   </code>
   
   2. <b> output for --split option </b>
   <pre>
   <code>
   <b> $ python extract_census_tracts_json.py --split </b>
       Namespace(convert=False, retrieve=False, split=True)
       
       All census tracts will be splited into single file based on FISP code placed in directory:
       <b>/home/cbrsdev/WINNF-GitHub/Spectrum-Access-System/data/census_tracts</b>

       Splitting files...
       
       <b>census_tract of fispCode:02013000100 record split to the file:/home/cbrsdev/WINNF-GitHub/Spectrum-Access-System/data/census_tracts/02013000100.json successfully</b>
       census_tract of fispCode:02016000200 record split to the file:/home/cbrsdev/WINNF-GitHub/Spectrum-Access-System/data/census_tracts/02016000200.json successfully
       census_tract of fispCode:02016000100 record split to the file:/home/cbrsdev/WINNF-GitHub/Spectrum-Access-System/data/census_tracts/02016000100.json successfully
       census_tract of fispCode:02240000100 record split to the file:/home/cbrsdev/WINNF-GitHub/Spectrum-Access-System/data/census_tracts/02240000100.json successfully
       .
       .
       .
       census_tract of fispCode:02020002823 record split to the file:/home/cbrsdev/WINNF-GitHub/Spectrum-Access-System/data/census_tracts/02020002823.json successfully
       <b>census_tract of fispCode:02020002900 record split to the file:/home/cbrsdev/WINNF-GitHub/Spectrum-Access-System/data/census_tracts/02020002900.json successfully</b>
   </pre>
   </code>

**Section to be completed**.
