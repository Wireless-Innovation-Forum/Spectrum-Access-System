#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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

""" This script retrieves the NLCD original geo data.

This is to be used in combination with `retile_nlcd.py` if ones want to recreate
the NLCD tiles from scratch.

WARNING: Files links have changed since the original extraction and processing
to produce official Winnforum version. It has not been tested if the new links
would produce exactly the same output.
"""
import os
import ssl
from six.moves import urllib


# Retrieves a resource via HTTP using urllib. Writes it to the filename
# in the current working directory. If the filename already exists in the
# current working directory, the method does not retrieve the remote file
# unless the 'force' parameter is set to True.
def RetrieveHTTPFile(resource, force=False, write_file=''):
  if not write_file:
    write_file = resource.split('/')[-1]

  if os.path.exists(write_file) and not force:
    print('Resource %s already retrieved' % resource)
    return

  context = ssl._create_unverified_context()
  f = urllib.request.urlopen(resource, context=context)
  if f.getcode() != 200:
    raise Exception('Could not find resource %s' % resource)
  with open(write_file, 'wb') as out:
    while True:
      c = f.read(64*1024)
      if not c:
        break
      out.write(c)
  f.close()


def RetrieveNlcdConus(directory):
  os.chdir(directory)
  print('Retrieving NLCD for CONUS...')
  # This is old link used to produce NLCD data for SAS v1.
  # This old link does not exist anymore
  RetrieveHTTPFile('http://www.landfire.gov/bulk/downloadfile.php?TYPE=nlcd2011&FNAME=nlcd_2011_landcover_2011_edition_2014_10_10.zip',
                   'nlcd_2011_landcover_2011_edition_2014_10_10.zip')
  # This is new data link, but the data seems to have been reprocessed as it is different from the
  # "2014" one.
  #RetrieveHTTPFile('https://s3-us-west-2.amazonaws.com/mrlc/NLCD_2011_Land_Cover_L48_20190424.zip',
  #                 write_file='NLCD_2011_Land_Cover_L48.zip')
  print('Retrieved NLCD for CONUS')

def RetrieveNlcdAlaska(directory):
  os.chdir(directory)
  print('Retrieving NLCD for Alaska...')
  RetrieveHTTPFile('https://s3-us-west-2.amazonaws.com/mrlc/ak_nlcd_2011_landcover_1_15_15.zip',
                   write_file='ak_nlcd_2011_landcover_1_15_15.zip')
  print('Retrieved NLCD for Alaska')

def RetrieveNlcdHawaii(directory):
  os.chdir(directory)
  print('Retrieving NLCD for Hawaii...')
  RetrieveHTTPFile('https://s3-us-west-2.amazonaws.com/mrlc/HI_landcover_wimperv_9-30-08_se5.zip',
                   write_file='HI_landcover_wimperv_9-30-08_se5.zip')
  print('Retrieved NLCD for Hawaii')

def RetrieveNlcdPuertoRico(directory):
  os.chdir(directory)
  print('Retrieving NLCD for Puerto-Rico...')
  RetrieveHTTPFile('https://s3-us-west-2.amazonaws.com/mrlc/PR_landcover_wimperv_10-28-08_se5.zip',
                   write_file='PR_landcover_wimperv_10-28-08_se5.zip')
  print('Retrieved NLCD for Puerto-Rico')


# Find the directory of this script.
cur_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.dirname(os.path.dirname(cur_dir))

dest_dir = os.path.join(root_dir, 'data', 'geo', 'orig_nlcd')
print('Retrieving NLCD files to dir=%s' % dest_dir)
if not os.path.exists(dest_dir):
  os.makedirs(dest_dir)

# Enable CONUS and Alaska if reprocessing need.
#RetrieveNlcdConus(dest_dir)
#RetrieveNlcdAlaska(dest_dir)
RetrieveNlcdHawaii(dest_dir)
RetrieveNlcdPuertoRico(dest_dir)
