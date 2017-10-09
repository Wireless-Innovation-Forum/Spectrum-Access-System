#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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

# this is a sample function to test the Monte Carlo aggregation simulation and compute the
# distribution of the aggregate received power.
# The devices as well as the receiver parameters are specified.
# It computes the 50th and 95th percentile aggregate power.
# Mayowa Aregbesola, Sep 2017

import os,sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from reference_models.monteCarlo import monteCarloSimITM
from reference_models.geo import vincenty

# Base data directory
_BASE_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '..', '..', '..', '..', 'data'))
				 
ITU_DIR = os.path.join(_BASE_DATA_DIR, 'itu')
TERRAIN_DIR = os.path.join(_BASE_DATA_DIR, 'geo', 'ned')

# Reconfigure the drivers to point to geo/testdata directories
monteCarloSimITM.ConfigureTerrainDriver(terrain_dir=TERRAIN_TEST_DIR)
monteCarloSimITM.ConfigureItuDrivers(itu_dir=ITU_TEST_DIR)

#define cdsd devices
device = {}
device ={}
device['maxEIRP'] = 30;
device['cntrFreq'] = 3625;
device['AntHeight'] = 10;

#define receivers
rx = {}
rx['Lat'] = 38.866667;
rx['Lon'] = -97.641667;
rx['AntHeight'] = 10;
rx['cntrFreq'] = 3625;

numCbsds = 500;     #number of CBSD devices
radius_start = 50;  # Distance of CBSD from rx

devices = [];
for i in range(numCbsds):
    bearing = 360.0*np.random.rand(1,1);
    device['Lat'], device['Lon'], alpha = vincenty.GeodesicPoint(rx['Lat'], rx['Lon'] , radius_start, bearing)
    devices.append(device)


mc50thp, mc95thp = monteCarloSimITM.aggregate(rx, devices)

print 'MC agg. 50thp = %3.3f dBm\n' % mc50thp
print 'MC agg. 95thp = %3.3f dBm\n' % mc95thp