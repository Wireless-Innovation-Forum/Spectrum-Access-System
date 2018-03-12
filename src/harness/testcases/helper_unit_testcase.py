import sas_testcase
import unittest
from util import compareDictWithUnorderedLists, areTwoPolygonsEqual
#===============================================================================
# this class unit tests AssertChannelsContainFrequencyRange method with different
# possible combinations for simplifying the tests we use frequencies in MHz units 
#===============================================================================
class AssertChannelsContainFrequencyRangeTest(sas_testcase.SasTestCase):
    
   def setUp(self):
    pass

   def test_shouldSucceedWhenConflictChannelWithEqualMin(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3555, 'highFrequency': 3570}}, 
                   {'frequencyRange' : {'lowFrequency': 3555, 'highFrequency': 3560}}, 
                   {'frequencyRange' : {'lowFrequency': 3560, 'highFrequency': 3575}}]
      
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}      
      self.assertChannelsContainFrequencyRange(channels, frequency_range)
      
   def test_shouldSucceedWhenOneChannelContainsAnother(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3565}},
                   {'frequencyRange' : {'lowFrequency': 3565, 'highFrequency': 3580}}, 
                   {'frequencyRange' : {'lowFrequency': 3570, 'highFrequency': 3575}}]
      
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3580}      
      self.assertChannelsContainFrequencyRange(channels, frequency_range)     
      
   def test_shouldSucceedWhenOneChannelContainsAnother2(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3565}},
                      {'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}}, 
                      {'frequencyRange' : {'lowFrequency': 3565, 'highFrequency': 3580}}]
      
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3580}      
      self.assertChannelsContainFrequencyRange(channels, frequency_range)    
      
   def test_shouldSucceedWhenConflictChannel(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3565, 'highFrequency': 3575}}, 
                   {'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3565}}]
      
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}      
      self.assertChannelsContainFrequencyRange(channels, frequency_range)
   
   def test_shouldSucceedWhenMultiSequencialChannel(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3560, 'highFrequency': 3565}},
                   {'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3565, 'highFrequency': 3580}}]
      
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3580}      
      self.assertChannelsContainFrequencyRange(channels, frequency_range)
    
   def test_shouldFailWhenChannelLowerThanRange(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3545, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3560, 'highFrequency': 3570}}, 
                   {'frequencyRange' : {'lowFrequency': 3570, 'highFrequency': 3575}}]
       
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}
      with self.assertRaises(AssertionError):    
        self.assertChannelsContainFrequencyRange(channels, frequency_range)

   def test_shouldFailWhenChannelHigherThanRange(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3560, 'highFrequency': 3570}}, 
                   {'frequencyRange' : {'lowFrequency': 3570, 'highFrequency': 3580}}]
       
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}
      with self.assertRaises(AssertionError):    
          self.assertChannelsContainFrequencyRange(channels, frequency_range)

   def test_shouldFailWhenMissingChannel(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3570, 'highFrequency': 3575}}, 
                   {'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3565}}]
       
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}
      with self.assertRaises(AssertionError):
          self.assertChannelsContainFrequencyRange(channels, frequency_range)

# Test the Compare Dict function in util which is used in FAD.1 test to compare PPA record and Esc records in dump file with injected object
class AssertPpaComparison(sas_testcase.SasTestCase):
    
   def setUp(self):
    pass

   def test_shouldSucceedComparingDictsOfPpas(self):
     ppa = {"zoneData":{"id":"zone/ppa/0/0","name":"PPA Zone 0","creator":"0","usage":"PPA","ppaInfo":{"PalId":["pal/05-2017/20041084200/A"],"PpaBeginDate":"2017-05-01T02:00:00Z","PpaExpirationDate":"2017-05-01T02:00:00Z","PpaLandCategory":"Cultivated Crops","PpaCenterLatitude":None,"PpaCenterLongitude":None},"zone":{"type":"FeatureCollection","features":[{"type":"Feature","properties":None,"geometry":{"type":"Geometry","coordinates":[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]]]}}]}}}

     same_ppa_with_different_order = {"zoneData":{"id":"zone/ppa/0/0","name":"PPA Zone 0","usage":"PPA","creator":"0","ppaInfo":{"PalId":["pal/05-2017/20041084200/A"],"PpaBeginDate":"2017-05-01T02:00:00Z","PpaExpirationDate":"2017-05-01T02:00:00Z","PpaLandCategory":"Cultivated Crops","PpaCenterLatitude":None,"PpaCenterLongitude":None},"zone":{"type":"FeatureCollection","features":[{"type":"Feature","properties":None,"geometry":{"type":"Geometry","coordinates":[[[38.8653748516116,-97.2386169433594]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]]]}}]}}}

     ppa_with_one_point_different = {"zoneData":{"id":"zone/ppa/0/0","name":"PPA Zone 0","creator":"0","usage":"PPA","ppaInfo":{"PalId":["pal/05-2017/20041084200/A"],"PpaBeginDate":"2017-05-01T02:00:00Z","PpaExpirationDate":"2017-05-01T02:00:00Z","PpaLandCategory":"Cultivated Crops","PpaCenterLatitude":None,"PpaCenterLongitude":None},"zone":{"type":"FeatureCollection","features":[{"type":"Feature","properties":None,"geometry":{"type":"Geometry","coordinates":[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.5386169433594]]]}}]}}}

     ppa_with_one_point_missing = {"zoneData":{"id":"zone/ppa/0/0","name":"PPA Zone 0","creator":"0","usage":"PPA","ppaInfo":{"PalId":["pal/05-2017/20041084200/A"],"PpaBeginDate":"2017-05-01T02:00:00Z","PpaExpirationDate":"2017-05-01T02:00:00Z","PpaLandCategory":"Cultivated Crops","PpaCenterLatitude":None,"PpaCenterLongitude":None},"zone":{"type":"FeatureCollection","features":[{"type":"Feature","properties":None,"geometry":{"type":"Geometry","coordinates":[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]]]}}]}}}

     ppa_with_creator_missing = {"zoneData":{"id":"zone/ppa/0/0","name":"PPA Zone 0","usage":"PPA","ppaInfo":{"PalId":["pal/05-2017/20041084200/A"],"PpaBeginDate":"2017-05-01T02:00:00Z","PpaExpirationDate":"2017-05-01T02:00:00Z","PpaLandCategory":"Cultivated Crops","PpaCenterLatitude":None,"PpaCenterLongitude":None},"zone":{"type":"FeatureCollection","features":[{"type":"Feature","properties":None,"geometry":{"type":"Geometry","coordinates":[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]]]}}]}}}

     ppa_with_creator_different = {"zoneData":{"id":"zone/ppa/0/0","name":"PPA Zone 0","creator":"1","usage":"PPA","ppaInfo":{"PalId":["pal/05-2017/20041084200/A"],"PpaBeginDate":"2017-05-01T02:00:00Z","PpaExpirationDate":"2017-05-01T02:00:00Z","PpaLandCategory":"Cultivated Crops","PpaCenterLatitude":None,"PpaCenterLongitude":None},"zone":{"type":"FeatureCollection","features":[{"type":"Feature","properties":None,"geometry":{"type":"Geometry","coordinates":[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]]]}}]}}}

     ppa_with_pal_id_different = {"zoneData":{"id":"zone/ppa/0/0","name":"PPA Zone 0","creator":"0","usage":"PPA","ppaInfo":{"PalId":["pal/05-2017/20041084202/A"],"PpaBeginDate":"2017-05-01T02:00:00Z","PpaExpirationDate":"2017-05-01T02:00:00Z","PpaLandCategory":"Cultivated Crops","PpaCenterLatitude":None,"PpaCenterLongitude":None},"zone":{"type":"FeatureCollection","features":[{"type":"Feature","properties":None,"geometry":{"type":"Geometry","coordinates":[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]]]}}]}}}

     self.assertTrue(compareDictWithUnorderedLists(ppa, same_ppa_with_different_order))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_one_point_different))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_one_point_missing))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_creator_missing))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_creator_different))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_pal_id_different))

     self.assertTrue(compareDictWithUnorderedLists(ppa, ppa))

class AssertPolygonComparison(sas_testcase.SasTestCase):
    
   def setUp(self):
    pass

   def test_shouldAreTwoPolygonsEqualWithSameOrderReturnTrue(self):
     c1 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348],[-107.40234375,44.43377984606822]]]
     c2 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348],[-107.40234375,44.43377984606822]]]
     self.assertTrue(areTwoPolygonsEqual(c1, c2, 0))

   def test_shouldAreTwoPolygonsEqualWithFirstPointNotEqualLastPointReturnFalse(self):
      c1 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348]]]
      c2 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348]]]
      self.assertFalse(areTwoPolygonsEqual(c1, c2, 0))

   def test_shouldAreTwoPolygonsEqualWithNotEqualLengthtReturnFalse(self):
      c1 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348],[-107.40234375,44.43377984606822]]]
      c2 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-107.40234375,44.43377984606822]]]
      self.assertFalse(areTwoPolygonsEqual(c1, c2, 0))

   def test_shouldAreTwoPolygonsEqualWithDifferentOrderReturnTrue(self):
     c1 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348],[-107.40234375,44.43377984606822]]]
     c2 = [[[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348],[-107.40234375,44.43377984606822], [-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573]]]
     self.assertTrue(areTwoPolygonsEqual(c1, c2, 0))

   def test_shouldAreTwoPolygonsEqualWithSameOrderOnePointDifferentReturnFalse(self):
     c1 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348],[-107.40234375,44.43377984606822]]]
     c2 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.534179,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348],[-107.40234375,44.43377984606822]]]
     self.assertFalse(areTwoPolygonsEqual(c1, c2, 0))

   def test_shouldAreTwoPolygonsEqualWithNotCorrectOrderReturnFalse(self):
     c1 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-107.5341796875,43.61221676817573],[-106.69921875,43.8028187190472],[-106.69921875,44.49650533109348],[-107.40234375,44.43377984606822]]]
     c2 = [[[-107.40234375,44.43377984606822],[-107.9296875,43.96119063892024],[-106.69921875,43.8028187190472],[-107.5341796875,43.61221676817573],[-106.69921875,44.49650533109348],[-107.40234375,44.43377984606822]]]
     self.assertFalse(areTwoPolygonsEqual(c1, c2, 0))

   def test_shouldAreTwoPolygonsEqualWithDeltaDifferenceReturnTrue(self):
     c1 = [[[0, 0],[1, 0],[0, 1],[1, 1],[0, 0]]]
     c2 = [[[0, 0],[1.1, 0.2],[-0.1, 1],[1, 1],[0, 0]]]
     self.assertTrue(areTwoPolygonsEqual(c1, c2, 0.2))
 
   def test_shouldAreTwoPolygonsEqualWithMoreThanDeltaDifferenceReturnFalse(self):
     c1 = [[[0, 0],[1, 0],[0, 1],[1, 1],[0, 0]]]
     c2 = [[[0, 0],[1.1, 0.2],[-0.1, 1],[1, 1],[0, 0]]]
     self.assertFalse(areTwoPolygonsEqual(c1, c2, 0.1))

   def test_shouldAreTwoPolygonsEqualWithTwoHolesReturnTrue(self):
     c1 = [[[0, 0],[1,0],[0, 1],[1, 1],[0, 0]], \
       [[0.5, 0.5],[0.5, 0.6],[0.6, 0.5, ],[0.6, 0.6],[0.5, 0.5]],\
       [[0.4, 0.4],[0.4, 0.5],[0.5, 0.5, ],[0.5, 0.4],[0.4, 0.4]]\
       ]
     c2 = [[[0, 0],[1,0],[0, 1],[1, 1],[0, 0]],\
       [[0.5, 0.5],[0.5, 0.6],[0.6, 0.5, ],[0.6, 0.6],[0.5, 0.5]],\
       [[0.4, 0.4],[0.4, 0.5],[0.5, 0.5, ],[0.5, 0.4],[0.4, 0.4]]\
       ]
     self.assertTrue(areTwoPolygonsEqual(c1, c2, 0))

   def test_shouldAreTwoPolygonsEqualWithTwoHolesInDifferentOrderReturnTrue(self):
     c1 = [[[0, 0],[1,0],[0, 1],[1, 1],[0, 0]], \
       [[0.5, 0.5],[0.5, 0.6],[0.6, 0.5, ],[0.6, 0.6],[0.5, 0.5]],\
       [[0.4, 0.4],[0.4, 0.5],[0.5, 0.5, ],[0.5, 0.4],[0.4, 0.4]]\
       ]
     c2 = [[[0, 0],[1,0],[0, 1],[1, 1],[0, 0]],\
       [[0.4, 0.4],[0.4, 0.5],[0.5, 0.5, ],[0.5, 0.4],[0.4, 0.4]],\
       [[0.5, 0.5],[0.5, 0.6],[0.6, 0.5, ],[0.6, 0.6],[0.5, 0.5]]\
       ]
     self.assertTrue(areTwoPolygonsEqual(c1, c2, 0))