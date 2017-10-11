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

# this function to test the Monte Carlo aggregation Simulation and computes the
# distribution of the aggregate received power.
# It loads the input data in testdata and computes the 50th and 95th percentile aggregate power.
# Mayowa Aregbesola, Sep 2017

import os,sys,json
from os import listdir
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from reference_models.geo import testutils
from reference_models.monteCarlo import monteCarloSimITM

expected_mc50thp = [-125.9370489,-128.6827196,-127.2109971,-126.0063689,-121.7983038,-125.3727378,-127.8123719,-127.0989529,-127.4656245,-126.9205056,-126.9298302,-124.2171575,-124.9990269,-125.0422774,-125.7674906,-124.7194184,-130.54093,-127.2899273,-126.6777794,-126.6505592]
expected_mc95thp = [-120.7074878,-124.587383,-123.2376229,-120.0524311,-116.3983079,-119.2219212,-121.8859048,-121.8583587,-122.4444883,-121.7158949,-121.3409275,-119.297393,-118.9688772,-119.1194921,-120.6633823,-119.7212828,-125.3493683,-121.8783857,-120.7174885,-121.4116367]

# Base data directory
_BASE_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '..', '..', '..', '..', 'data'))

ITU_DIR = os.path.join(_BASE_DATA_DIR, 'itu')
TERRAIN_DIR = os.path.join(_BASE_DATA_DIR, 'geo', 'ned')

def load_files(testfiles, testpath):
    Tests = []
    for testfile in testfiles:
        test = json.load(open(os.path.join(testpath, testfile)))
        Tests.append(test)
    return Tests

class TestAggregation(unittest.TestCase):

    @classmethod
    def setUp(self):

        # Reconfigure the drivers to point to geo/testdata directories
        monteCarloSimITM.ConfigureTerrainDriver(terrain_dir=TERRAIN_TEST_DIR)
        monteCarloSimITM.ConfigureItuDrivers(itu_dir=ITU_TEST_DIR)
    
    def test_aggregation(self):
        testpath = 'testdata'
        testfiles = [f for f in listdir(testpath) if os.path.isfile(os.path.join(testpath, f))]
        Tests = load_files(testfiles, testpath)
        i = 0
        for test in Tests:
            
            rx = test['rx']
            txdevices = test['tx']
            N = int(1e4);    

            mc50thp, mc95thp = monteCarloSimITM.aggregate(rx, txdevices)
            self.assertAlmostEqual(mc50thp, expected_mc50thp[i], 4)
            self.assertAlmostEqual(mc95thp, expected_mc95thp[i], 4)
            i += 1

if __name__ == '__main__':
    unittest.main()