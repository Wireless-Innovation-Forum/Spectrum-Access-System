#    Copyright 2018 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
"""
 All the USGS census tract data are stored in one census tract per file in geojson format
 with the file name being the fips code (aka. GEOID in the census tract data term) of
 the corresponding census tract.
 For example, for a census tract with
     "STATEFP"="20","COUNTYFP"="063","TRACTCE"="955100","GEOID"="20063955100",
   the file name is 20063955100.json.

 1. Clone the SAS-Data repository
     git clone https://github.com/Wireless-Innovation-Forum/SAS-Data.git
 2. Extracting the census tract zip file
    To actually unzip the census tract json files from the zip file,
    you can use the provided script 'extract_census_tracts_json.py':

    $ python extract_census_tracts_json.py

    This will extract all the census tract json files from the zip file to
    Spectrum-Access-System/data/census_tracts directory.


"""
from reference_models.geo import census_tract
import os

# Find the census_tracts directory
dir = os.path.dirname(os.path.realpath(__file__))
root_directory = os.path.dirname(os.path.dirname(dir))
dest_directory = os.path.join(os.path.join(root_directory, 'data'), 'census_tracts')
print 'All census tracts will be extracted in directory:%s' % dest_directory
if not os.path.exists(dest_directory):
  os.makedirs(dest_directory)

# Initialize the CensusTractDriver.
census_tract_driver = census_tract.CensusTractDriver()

# Set the destination directory in Census Tract Driver.
census_tract_driver.SetCensusTractDirectory(dest_directory)
zip_file_name = 'census26.zip'
fisp_code_list = ['20063955100.json', '20063955200.json']

# Extract the specific fispcode.json from specific census_tracts zipped file.
# census_tract_driver.ExtractData() will extract all zipped files without any filter.
census_tract_driver.ExtractData(zip_filename=zip_file_name,
                                fisp_codelist=fisp_code_list)
