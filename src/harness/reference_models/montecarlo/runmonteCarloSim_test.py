import os,sys,json
import numpy as np
from os import listdir


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from reference_models.geo import testutils
from reference_models.geo import tropoclim
from reference_models.geo import refractivity
from reference_models.geo import terrain
from reference_models.geo import vincenty
from reference_models.propagation.itm import itm
from reference_models.monteCarlo import monteCarloSimITM

expected_mc50thp = [-125.9370489,-128.6827196,-127.2109971,-126.0063689,-121.7983038,-125.3727378,-127.8123719,-127.0989529,-127.4656245,-126.9205056,-126.9298302,-124.2171575,-124.9990269,-125.0422774,-125.7674906,-124.7194184,-130.54093,-127.2899273,-126.6777794,-126.6505592]
expected_mc95thp = [-120.7074878,-124.587383,-123.2376229,-120.0524311,-116.3983079,-119.2219212,-121.8859048,-121.8583587,-122.4444883,-121.7158949,-121.3409275,-119.297393,-118.9688772,-119.1194921,-120.6633823,-119.7212828,-125.3493683,-121.8783857,-120.7174885,-121.4116367]


def load_files(testfiles, testpath):
    Tests = []
    for testfile in testfiles:
        test = json.load(open(os.path.join(testpath, testfile)))
        Tests.append(test)
    return Tests

class TestAggregation():

    @classmethod
    def setUp(self):
        TERRAIN_TEST_DIR = "C:/Databases/Terrain"
        ITU_TEST_DIR = os.path.join(os.path.dirname(__file__),'..', 'geo', 'testdata', 'itu')
        
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
            numDevices = test['numdevices']
            
            conf = 0.5
            prop_model_rel =0.5
            dielect = 25;
            conductivity = 0.02  #Conductivity (always 0.02)
            polarization = int(1) # Polarization (always vertical = 1)
            mdvar = 13
            
            N = int(1e4);    
            sampAggregateRxPowLin =  np.zeros(N)
            sampMedian_all_distributions_dBm =  np.zeros(N)
        
            numdevice= 0;
            mc50BPDF, mc95thp = monteCarloSimITM.aggregate(rx, txdevices)
            print mc50BPDF, mc95thp
            i += 1

A = TestAggregation()
A.setUp()
A.test_aggregation()