#    Copyright 2015 SAS Project Authors. All Rights Reserved.
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

# This script retrieves the IBFS database files from the FCC FTP site, writing
# them into the data/ibfs directory. If the .zip files already exist, the
# scirpt will download files if they are newer than the local versions.

import ftputil
import os

# Fetch via FTP all the 2010 census tract state shapefiles. Writes them
# to the current directory.
def RetrieveIBFS():
  fcc = ftputil.FTPHost('ftp.fcc.gov', 'anonymous', '')

  print 'Downloading IBFS.zip database file'
  fcc.download_if_newer('pub/Bureaus/International/databases/IBFS.zip', 'IBFS.zip')
  fcc.close()

  print 'Downloading ibfs.txt schema'
  fcc.download_if_newer('pub/Bureaus/International/databases/ibfs.txt', 'ibfs.txt')

# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dest = os.path.join(os.path.join(rootDir, 'data'), 'ibfs')
print 'Retrieving IBFS database files to dir=%s' % dest
if not os.path.exists(dest):
  os.makedirs(dest)
os.chdir(dest)
RetrieveIBFS()

