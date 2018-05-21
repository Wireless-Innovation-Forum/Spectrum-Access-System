import sas_testcase
import unittest
from util import compareDictWithUnorderedLists
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

# ===============================================================================
# this class unit tests assertChannelsOverlapFrequencyRange method with different
# possible combinations for simplifying the tests we use frequencies in MHz units
# ===============================================================================
class assertChannelsOverlapFrequencyRange(sas_testcase.SasTestCase):

    def setUp(self):
        pass

    # test cases for testing constraint_low=True

    def test_shouldSucceedWhenSingleChannelCoversAllConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3700}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3650}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldSucceedWhenMultipleChannelsCoverAllConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3620}},
                    {'frequencyRange': {'lowFrequency': 3620, 'highFrequency': 3630}},
                    {'frequencyRange': {'lowFrequency': 3630, 'highFrequency': 3650}},
                    {'frequencyRange': {'lowFrequency': 3650, 'highFrequency': 3700}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3660}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldSucceedWhenConflictChannelWithEqualMinConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3555, 'highFrequency': 3570}},
                    {'frequencyRange': {'lowFrequency': 3555, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3560, 'highFrequency': 3575}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldSucceedWhenOneChannelContainsAnotherConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3565}},
                    {'frequencyRange': {'lowFrequency': 3565, 'highFrequency': 3580}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3575}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3580}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldSucceedWhenOneChannelContainsAnotherConstrainLow2(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3565}},
                    {'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3565, 'highFrequency': 3580}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3580}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldSucceedWhenConflictChannelConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3565, 'highFrequency': 3575}},
                    {'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3565}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldSucceedWhenMultiSequencialChannelConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3560, 'highFrequency': 3565}},
                    {'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3565, 'highFrequency': 3580}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3580}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldSuccessWhenChannelHigherThanRangeConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3560, 'highFrequency': 3570}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3580}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldFailWhenChannelLowerThanRangeConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3545, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3560, 'highFrequency': 3570}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3575}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        with self.assertRaises(AssertionError):
            self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldFailWhenChannelOutOfLowRangeConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3450, 'highFrequency': 3460}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3575}},
                    {'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3565}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        with self.assertRaises(AssertionError):
            self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    def test_shouldFailWhenChannelOutOfHighRangeConstrainLow(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3575}},
                    {'frequencyRange': {'lowFrequency': 3590, 'highFrequency': 3600}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        with self.assertRaises(AssertionError):
            self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=False)

    # Test cases for testing constraint_high=True

    def test_shouldSucceedWhenSingleChannelCoversAllConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3650}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3650}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=True)

    def test_shouldSucceedWhenMultipleChannelsCoverAllConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3620}},
                    {'frequencyRange': {'lowFrequency': 3620, 'highFrequency': 3630}},
                    {'frequencyRange': {'lowFrequency': 3630, 'highFrequency': 3650}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3650}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, cconstrain_low=False, constrain_high=True)

    def test_shouldSucceedWhenConflictChannelWithEqualMinConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3555, 'highFrequency': 3570}},
                    {'frequencyRange': {'lowFrequency': 3555, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3560, 'highFrequency': 3575}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, cconstrain_low=False, constrain_high=True)

    def test_shouldSucceedWhenOneChannelContainsAnotherConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3565}},
                    {'frequencyRange': {'lowFrequency': 3565, 'highFrequency': 3580}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3575}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3580}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=True)

    def test_shouldSucceedWhenOneChannelContainsAnotherConstrainHigh2(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3565}},
                    {'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3565, 'highFrequency': 3580}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3580}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=True)

    def test_shouldSucceedWhenConflictChannelConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3565, 'highFrequency': 3575}},
                    {'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3565}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=True)

    def test_shouldSucceedWhenMultiSequencialChannelConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3560, 'highFrequency': 3565}},
                    {'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3565, 'highFrequency': 3580}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3580}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=True)

    def test_shouldSuccessWhenChannelLowerThanRangeConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3570}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3580}}]

        frequency_range = {'lowFrequency': 3560, 'highFrequency': 3580}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=True)

    def test_shouldFailWhenChannelHigherThanRangeConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3560, 'highFrequency': 3570}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3580}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        with self.assertRaises(AssertionError):
            self.assertChannelsOverlapFrequencyRange(channels, frequency_range, cconstrain_low=False, constrain_high=True)

    def test_shouldFailWhenChannelOutOfLowRangeConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3450, 'highFrequency': 3460}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3575}},
                    {'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3565}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        with self.assertRaises(AssertionError):
            self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=True)

    def test_shouldFailWhenChannelOutOfHighRangeConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3550, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3575}},
                    {'frequencyRange': {'lowFrequency': 3590, 'highFrequency': 3600}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        with self.assertRaises(AssertionError):
            self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=True)

    # Test cases for testing constraint_high=False and constraint_high=False

    def test_shouldSucceedWhenSingleChannelCoversAllConstrainNeither(self):
        channels = [{'frequencyRange': {'lowFrequency': 3540, 'highFrequency': 3700}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3650}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=False)

    def test_shouldSucceedWhenMultipleChannelsCoverAllConstrainNeither(self):
        channels = [{'frequencyRange': {'lowFrequency': 3540, 'highFrequency': 3620}},
                    {'frequencyRange': {'lowFrequency': 3620, 'highFrequency': 3630}},
                    {'frequencyRange': {'lowFrequency': 3630, 'highFrequency': 3700}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3650}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=False)

    def test_shouldSucceedWhenConflictChannelWithEqualMinConstrainNeither(self):
        channels = [{'frequencyRange': {'lowFrequency': 3540, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3555, 'highFrequency': 3570}},
                    {'frequencyRange': {'lowFrequency': 3555, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3560, 'highFrequency': 3595}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=False, constrain_high=False)

    # Test cases for testing constraint_high=True and constraint_high=True

    def test_shouldFailWhenChannelOutOfRangeConstrainHigh(self):
        channels = [{'frequencyRange': {'lowFrequency': 3540, 'highFrequency': 3560}},
                    {'frequencyRange': {'lowFrequency': 3560, 'highFrequency': 3570}},
                    {'frequencyRange': {'lowFrequency': 3570, 'highFrequency': 3580}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        with self.assertRaises(AssertionError):
            self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=True)

    def test_shouldFailWhenChannelOutOfRangeConstrainHigh2(self):
        channels = [{'frequencyRange': {'lowFrequency': 3540, 'highFrequency': 3580}}]

        frequency_range = {'lowFrequency': 3550, 'highFrequency': 3575}
        with self.assertRaises(AssertionError):
            self.assertChannelsOverlapFrequencyRange(channels, frequency_range, constrain_low=True, constrain_high=True)

# Test the Compare Dict function in util which is used in FAD.1 test to compare PPA record and Esc records in dump file with injected object
class AssertPpaComparison(sas_testcase.SasTestCase):
    
   def setUp(self):
    pass

   def test_shouldSucceedComparingDictsOfPpas(self):
     ppa = {'zoneData':{'id':'zone/ppa/0/0','name':'PPA Zone 0','creator':'0','usage':'PPA','ppaInfo':{'PalId':['pal/05-2017/20041084200/A'],'PpaBeginDate':'2017-05-01T02:00:00Z','PpaExpirationDate':'2017-05-01T02:00:00Z','PpaLandCategory':'Cultivated Crops','PpaCenterLatitude':None,'PpaCenterLongitude':None},'zone':{'type':'FeatureCollection','features':[{'type':'Feature','properties':None,'geometry':{'type':'Geometry','coordinates':[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]]]}}]}}}

     same_ppa_with_different_order = {'zoneData':{'id':'zone/ppa/0/0','name':'PPA Zone 0','usage':'PPA','creator':'0','ppaInfo':{'PalId':['pal/05-2017/20041084200/A'],'PpaBeginDate':'2017-05-01T02:00:00Z','PpaExpirationDate':'2017-05-01T02:00:00Z','PpaLandCategory':'Cultivated Crops','PpaCenterLatitude':None,'PpaCenterLongitude':None},'zone':{'type':'FeatureCollection','features':[{'type':'Feature','properties':None,'geometry':{'type':'Geometry','coordinates':[[[38.8653748516116,-97.2386169433594]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]]]}}]}}}

     ppa_with_one_point_different = {'zoneData':{'id':'zone/ppa/0/0','name':'PPA Zone 0','creator':'0','usage':'PPA','ppaInfo':{'PalId':['pal/05-2017/20041084200/A'],'PpaBeginDate':'2017-05-01T02:00:00Z','PpaExpirationDate':'2017-05-01T02:00:00Z','PpaLandCategory':'Cultivated Crops','PpaCenterLatitude':None,'PpaCenterLongitude':None},'zone':{'type':'FeatureCollection','features':[{'type':'Feature','properties':None,'geometry':{'type':'Geometry','coordinates':[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.5386169433594]]]}}]}}}

     ppa_with_one_point_missing = {'zoneData':{'id':'zone/ppa/0/0','name':'PPA Zone 0','creator':'0','usage':'PPA','ppaInfo':{'PalId':['pal/05-2017/20041084200/A'],'PpaBeginDate':'2017-05-01T02:00:00Z','PpaExpirationDate':'2017-05-01T02:00:00Z','PpaLandCategory':'Cultivated Crops','PpaCenterLatitude':None,'PpaCenterLongitude':None},'zone':{'type':'FeatureCollection','features':[{'type':'Feature','properties':None,'geometry':{'type':'Geometry','coordinates':[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]]]}}]}}}

     ppa_with_creator_missing = {'zoneData':{'id':'zone/ppa/0/0','name':'PPA Zone 0','usage':'PPA','ppaInfo':{'PalId':['pal/05-2017/20041084200/A'],'PpaBeginDate':'2017-05-01T02:00:00Z','PpaExpirationDate':'2017-05-01T02:00:00Z','PpaLandCategory':'Cultivated Crops','PpaCenterLatitude':None,'PpaCenterLongitude':None},'zone':{'type':'FeatureCollection','features':[{'type':'Feature','properties':None,'geometry':{'type':'Geometry','coordinates':[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]]]}}]}}}

     ppa_with_creator_different = {'zoneData':{'id':'zone/ppa/0/0','name':'PPA Zone 0','creator':'1','usage':'PPA','ppaInfo':{'PalId':['pal/05-2017/20041084200/A'],'PpaBeginDate':'2017-05-01T02:00:00Z','PpaExpirationDate':'2017-05-01T02:00:00Z','PpaLandCategory':'Cultivated Crops','PpaCenterLatitude':None,'PpaCenterLongitude':None},'zone':{'type':'FeatureCollection','features':[{'type':'Feature','properties':None,'geometry':{'type':'Geometry','coordinates':[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]]]}}]}}}

     ppa_with_pal_id_different = {'zoneData':{'id':'zone/ppa/0/0','name':'PPA Zone 0','creator':'0','usage':'PPA','ppaInfo':{'PalId':['pal/05-2017/20041084202/A'],'PpaBeginDate':'2017-05-01T02:00:00Z','PpaExpirationDate':'2017-05-01T02:00:00Z','PpaLandCategory':'Cultivated Crops','PpaCenterLatitude':None,'PpaCenterLongitude':None},'zone':{'type':'FeatureCollection','features':[{'type':'Feature','properties':None,'geometry':{'type':'Geometry','coordinates':[[[38.8653748516116,-97.2386169433594]],[[38.7615795117574,-97.3196411132812]],[[38.7390884418769,-97.1699523925781]],[[38.867513370012,-97.1617126464844]],[[38.8653748516116,-97.2386169433594]]]}}]}}}

     self.assertTrue(compareDictWithUnorderedLists(ppa, same_ppa_with_different_order))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_one_point_different))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_one_point_missing))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_creator_missing))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_creator_different))

     self.assertFalse(compareDictWithUnorderedLists(ppa, ppa_with_pal_id_different))

     self.assertTrue(compareDictWithUnorderedLists(ppa, ppa))

if __name__ == '__main__':
  unittest.main()
