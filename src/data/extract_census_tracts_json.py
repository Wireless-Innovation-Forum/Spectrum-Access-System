#    Copyright 2016-2018 SAS Project Authors. All Rights Reserved.
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
"""extract_census_tracts utility to download and convert the census_tract and split to single file.

This extract_census_tracts_json.py will help to perform following operations:
1.Download original census tract data from the USGS web site  by providing the
 command line option --retrieve
2.Convert the shape file to GeoJSON by providing the command line option --convert
3.Split the GeoJSON file into individual census tract files by providing the command line
 option --split
'Spectrum-Access-System/data/census' directory will be created/used to download original
 census tract data and convert the shape file to geojson for the option #1 and #2.
'Spectrum-Access-System/data/census_tracts' directory will be created/used to split the
 geojson file into individual census_tract by prefix GEOID as file name.

"""
import argparse
import os
import re
import sys
import glob
import json
import ftputil
from reference_models.geo import census_tract

def FindStateTractFilenames(census):
  """Retrieve the desired state-level census tract zip files from the census FTP site."""
  files = census.listdir('geo/tiger/TIGER2010/TRACT/2010/')
  print 'Found %d files in census ftp dir' % len(files)
  matches = []
  for f in files:
    if re.match(r'tl_2010_\d\d_tract10.zip$', f):
      matches.append(f)
  print 'Found %d matching state files in census tract ftp dir' % len(matches)
  return matches

# Fetch via FTP all the 2010 census tract state shapefiles. Writes them
# to the current directory.
def RetrieveShapefiles(directory):
  """Retrieve all the 2010 census tract state shapefiles and dumps to the current directory."""
  os.chdir(directory)
  census = ftputil.FTPHost('ftp2.census.gov', 'anonymous', '')
  files = FindStateTractFilenames(census)

  for f in files:
    print 'Downloading %s' % f
    census.download_if_newer('geo/tiger/TIGER2010/TRACT/2010/' + f, f)
  census.close()

def ConvertShapefilesToGeoJson(directory):
  """Convert Shapefile to GeoJson file with the help of CensusTractDriver."""
  # Initialize the CensusTractDriver.
  census_tract_driver = census_tract.CensusTractDriver()

  # Set the destination directory in Census Tract Driver.
  census_tract_driver.SetCensusTractDirectory(directory)

  # Convert ShapelyFile to GeoJson
  census_tract_driver.ConvertShapelyFileToGeoJSON()

def SplitCensusTractsGeoJsonFile(source_directory, destination_directory):
  """Split Census Tracts GeoJson file with mulitiple single file based on FISP Code."""
  try:
    print "\n" + "Splitting files..." + "\n"
    os.chdir(source_directory)
    file_data = glob.glob('*.json')
    x = file_data
    for files in x:
      info = open(files, 'r').read()
      geojs = json.loads(info)
      features = geojs['features']
      # split all census_tracts based on FISP code and dump into separate directory
      # census_tract_directory
      os.chdir(destination_directory)

      for feature in features:
        fisp_code = None
        # Check for properties object that includes the field GEOIDXX and get that value
        # of GEOIDXX and assign it as file_name to split GeoJSON records.
        for field_name in feature['properties']:
           if field_name.startswith('GEOID'):
             fisp_code = feature['properties'][field_name]
             break
        if not fisp_code:
          raise Exception('Unable to find GEOID property in census tracts')
        file_name = fisp_code + '.json'
        with open(file_name, 'w') as file_handle:
          file_handle.write(json.dumps(feature))
        print "census_tract of fispCode:%s record split to the file:%s " \
              "successfully" % (fisp_code,
                                os.path.join(destination_directory, file_name))
  except Exception as err:
    print "There is issue in split CensusTracts file to single file :%s" % err.message

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument(
      '--retrieve', help='Download original census tract data from the USGS web site.',
      dest='retrieve', action='store_true')
  group.add_argument(
      '--convert', help='Convert the shape file to GeoJSON.',
      dest='convert', action='store_true')
  group.add_argument(
      '--split', help='Split census tract files into individual based on FISP code.',
      dest='split', action='store_true')
  try:
    args = parser.parse_args()
    print args
  except:
    parser.print_help()
    sys.exit(0)

  # Find the census_tracts and census directory and
  # create the directory if not exists.
  root_directory = os.path.dirname(os.path.dirname(os.path.dirname(
      os.path.realpath(__file__))))
  census_directory = os.path.join(os.path.join(root_directory, 'data'),
                                  'census')
  census_tract_directory = os.path.join(os.path.join(root_directory, 'data'),
                                        'census_tracts')

  if args.retrieve:
    # Retrieve Census tracts shapely files from FTP site/
    print 'Downloading census shapefiles from USGS site to directory=%s' % census_directory
    if not os.path.exists(census_directory):
      os.makedirs(census_directory)
    RetrieveShapefiles(census_directory)

  if args.convert:
    # Convert the shapely file to GeoJSON format.
    print 'All census tracts will be converted into GeoJSON and placed ' \
          'in directory:%s' % census_directory
    ConvertShapefilesToGeoJson(census_directory)

  if args.split:
    print 'All census tracts will be splited into single file based on FISP code placed ' \
          'in directory:%s' % census_tract_directory
    if not os.path.exists(census_tract_directory):
      os.makedirs(census_tract_directory)

    SplitCensusTractsGeoJsonFile(census_directory, census_tract_directory)
