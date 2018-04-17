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

"""Driver for access to Census tract data.
"""
import json
import os
import zipfile

from reference_models.geo import CONFIG


class CensusTractDriver:
  def __init__(self, census_tract_directory=None):
    self.SetCensusTractDirectory(census_tract_directory)

  def SetCensusTractDirectory(self, census_tract_directory):
    """Configures the Census Tracts data directory."""
    self._census_tract_dir = census_tract_directory
    if self._census_tract_dir is None:
      self._census_tract_dir = CONFIG.GetCensusTractsDir()

  def GetCensusTract(self, fips_code):
    """Returns the census tract (as a Python object) for the given fips code (as a str)."""
    fips_code = str(fips_code)
    census_tract_file_path = os.path.join(self._census_tract_dir, "%s.json" % fips_code)
    if os.path.exists(census_tract_file_path):
      with open(census_tract_file_path, 'r') as census_tract_file:
        try:
          return json.load(census_tract_file)
        except:
          raise IOError('Error occurred in opening Census Tract File: %s' % census_tract_file.name)
    else:
      raise Exception("Census Tract data not found with FIPS Code: %s" % fips_code)

  def ExtractData(self, zip_filename=None, fisp_codelist=None):
    """Extracts the all fisp code matched json file present in specific zip file or all files."""
    error_occured = False

    # Filter the zip filename based on specified file name if any endswith .zip
    census_tracts_file_list = [os.path.join(self._census_tract_dir, f)
                               for f in os.listdir(self._census_tract_dir)
                               if all((True if not zip_filename else
                                       f.startswith(zip_file_name),
                                       f.endswith('.zip')))]
    if not census_tracts_file_list:
      print 'Please specify the correct zip file name or clone SAS-Data directory before' \
            'execute this script'
      error_occured = True

    # Filter the files matches with fisp_code in all downloaded zipped file and matched files
    # will be extracted.
    for file_name in census_tracts_file_list:
        # Check if already extracted
        zf = zipfile.ZipFile(file_name, 'r')

        #Only fisp_code matched json files are fetched from specified zip file if it is specified.
        #if fisp_codes are not specified then all the json files from either specific zipfile
        #or all zipped file that containing the json files will be returned.
        fisp_code_matched_files = [datfile
                                   for datfile in zf.infolist()
                                   if all((datfile.filename.endswith('.json'),
                                           True if not fisp_code_list else datfile.filename in
                                           fisp_codelist))]
        if fisp_code_matched_files:
          break

    if not fisp_code_matched_files:
      print 'No fisp code matched files present in zip file. Please verify the inputs'
      error_occured = True

    for datfile in fisp_code_matched_files:
      try:
        zf.extract(datfile, self._census_tract_dir)
        print '%s is extracted successfully in %s' % (datfile.filename,
                                                      self._census_tract_dir)
      except Exception as err:
        error_occured = True
        print "Exception:%s" % err.message
        print 'Cannot extract ' + datfile.filename + ' from ' + os.path.dirname(
            datfile.filename)

    # Check is there any exception while extracting the files.
    if not error_occured:
       print 'SUCCESS: All requested files which are matched with fisp code ' \
             'are extracted successfully'
    else:
       print 'FAILURE: There is an exception while extracting some of the files \n or '  \
             'No matched files are returned.\n ' \
             'Please specify the correct zip file name or clone SAS-Data directory before' \
             'execute this script'

# Set the Base data directory
_BASE_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '..', '..', '..', '..', 'data'))
# Set the census directory
CENSUS_TRACTS_DIR = os.path.join(_BASE_DATA_DIR, 'census_tracts')
census_tract_driver = CensusTractDriver()
census_tract_driver.SetCensusTractDirectory(CENSUS_TRACTS_DIR)
zip_file_name = 'census26.zip'
fisp_code_list = ['20063955100.json', '20063955200.json']
census_tract_driver.ExtractData(zip_filename=zip_file_name,
                                fisp_codelist=fisp_code_list)
