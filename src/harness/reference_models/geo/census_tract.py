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
import io
import re
import glob
import shapefile
from reference_models.geo import CONFIG

class CensusTractDriver(object):
  def __init__(self, census_tract_directory=None):
    self.SetCensusTractDirectory(census_tract_directory)

  def SetCensusTractDirectory(self, census_tract_directory):
    """Configures the Census Tracts data directory."""
    self._census_tract_dir = census_tract_directory
    if self._census_tract_dir is None:
      self._census_tract_dir = CONFIG.GetCensusTractsDir()

  def GetCensusTract(self, fips_code):
    """Returns the census tract (as a Python object) for the given FIPS code (as a str)."""
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

  def __ExtractZipFiles(self, zip_filename=None):
    """Extract the census tracts file downloaded from USGS site."""
    # Filter the zip filename based on specified file name if any ends with .zip
    census_tracts_file_list = [os.path.join(self._census_tract_dir, f)
                               for f in os.listdir(self._census_tract_dir)
                               if all((True if not zip_filename else
                                       f.startswith(zip_filename),
                                       f.endswith('.zip')))]
    for file_name in census_tracts_file_list:
      # Check if already extracted.
      zf = zipfile.ZipFile(file_name, 'r')
      for datfile in zf.infolist():
        if any((datfile.filename.endswith('.dbf'),
                datfile.filename.endswith('.prj'),
                datfile.filename.endswith('.shp'),
                datfile.filename.endswith('.shp.xml'),
                datfile.filename.endswith('.shx'))):
          try:
            zf.extract(datfile, self._census_tract_dir)
          except:
            raise Exception('Cannot extract ' + datfile.filename +
                            ' from ' + zip_filename)


  def __ProcessShapelyFile(self, file_name):
    """Verify the format for shpely file and and extracts and convert to GeoJSON format."""
    basename = os.path.splitext(os.path.basename(file_name))[0]
    print 'Processing shp file %s' % basename
    with zipfile.ZipFile(file_name) as zf:
      shpfile = io.BytesIO(zf.read(basename + '.shp'))
      dbffile = io.BytesIO(zf.read(basename + '.dbf'))
      shxfile = io.BytesIO(zf.read(basename + '.shx'))

    shpfile = shapefile.Reader(shp=shpfile, shx=shxfile, dbf=dbffile)
    geoid_field = -1
    aland_field = -1
    awater_field = -1
    # light check to ensure that necessary fields are present in shapefile.
    for i in range(0, len(shpfile.fields)):
      field = shpfile.fields[i][0]
      if 'GEOID' in field:
        geoid_field = i - 1
      elif 'ALAND' in field:
        aland_field = i - 1
      elif 'AWATER' in field:
        awater_field = i - 1
    if geoid_field == -1 or aland_field == -1 or awater_field == -1:
      raise Exception('Could not find GEOID,ALAND,AWATER in fields %s' % shpfile.fields)

    # Extract all files before convert to shapely.
    self.__ExtractZipFiles()

    # Proceed further to convert to geojson.
    os.chdir(self._census_tract_dir)
    file_data = glob.glob('*.shp')
    x = file_data
    print x
    try:
      for files in x:
        # Read the shapefile.
        reader = shapefile.Reader(files)
        fields = reader.fields[1:]
        field_names = [field[0] for field in fields]
        records = []
        for sr in reader.shapeRecords():
          atr = dict(zip(field_names, sr.record))
          geom = sr.shape.__geo_interface__
          records.append(dict(type="Feature", geometry=geom, properties=atr))

        # Write the GeoJSON file.
        jsonfile = files.replace(".shp", ".json")
        geojson = open(jsonfile, "w")
        geojson.write(json.dumps({"type": "FeatureCollection",
                                  "features": records}, indent=2) + "\n")
        geojson.close()
        print "\n" + files + " was converted to " + jsonfile + "."
    except Exception as err:
       print "There is an issue in convertShapelyfile to GeoJson:%s" % err.message

  def ConvertShapelyFileToGeoJSON(self):
    """Convert the ShapelyFile to GeoJson format."""
    print "Convert the ShapelyFile to GeoJson format"
    files = os.listdir(self._census_tract_dir)
    print 'Found %d zip files to translate' % len(files)
    for f in files:
      if os.path.isfile(os.path.join(self._census_tract_dir, f)) and re.match(r'.*\.zip$', f):
        self.__ProcessShapelyFile(os.path.join(self._census_tract_dir, f))

  def ExtractData(self, zip_filename=None, fips_codelist=None):
    """Extract the all FIPS code matched json file present in specific zip file or all files."""
    error_occured = False

    # Filter the zip filename based on specified file name if any ends with .zip
    census_tracts_file_list = [os.path.join(self._census_tract_dir, f)
                               for f in os.listdir(self._census_tract_dir)
                               if all((True if not zip_filename else
                                       f.startswith(zip_filename),
                                       f.endswith('.zip')))]
    if not census_tracts_file_list:
      print 'Please specify the correct zip file name or clone SAS-Data directory \n ' \
            'before executing this script'
      error_occured = True
      fips_code_matched_files = []

    # Filter the files matches with fips_code in all downloaded zipped file and matched files
    # will be extracted.
    for file_name in census_tracts_file_list:
        # Check if already extracted
        zf = zipfile.ZipFile(file_name, 'r')

        #Only fips_code matched json files are fetched from specified zip file if it is specified.
        #if fips_codes are not specified then all the json files from either specific zipfile
        #or all zipped file that containing the json files will be returned.
        fips_code_matched_files = [datfile
                                   for datfile in zf.infolist()
                                   if all((datfile.filename.endswith('.json'),
                                           True if not fips_codelist else datfile.filename in
                                           fips_codelist))]
        if fips_code_matched_files:
          break

    if not fips_code_matched_files:
      print 'No FIPS code matched files present in zip file. Please verify the inputs'
      error_occured = True

    for datfile in fips_code_matched_files:
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
       print 'SUCCESS: All requested files which are matched with FIPS code ' \
             'are extracted successfully'
    else:
       print 'FAILURE: There is an exception while extracting some of the files \n or '  \
             'No matched files are returned.\n ' \
             'Please specify the correct zip file name or clone SAS-Data directory \n ' \
             'before executing this script'
