import sas_testcase
import unittest

class HelperFunctionUnitTest(sas_testcase.SasTestCase):
    
   def setUp(self):
    pass

   def test_assertChannelsContainFrequencyRangeShouldSucceedWhenConflictChannelWihtEqualMin(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3555, 'highFrequency': 3570}}, 
                   {'frequencyRange' : {'lowFrequency': 3555, 'highFrequency': 3560}}, 
                   {'frequencyRange' : {'lowFrequency': 3560, 'highFrequency': 3575}}]
      
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}      
      self.assertChannelsContainFrequencyRange(channels, frequency_range)
      
   def test_assertChannelsContainFrequencyRangeShouldSucceedWhenConflictChannel(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3565, 'highFrequency': 3575}}, 
                   {'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3565}}]
      
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}      
      self.assertChannelsContainFrequencyRange(channels, frequency_range)
   
   def test_assertChannelsContainFrequencyRangeShouldSucceedWhenMultiSequencialChannel(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3560, 'highFrequency': 3565}},
                   {'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3565, 'highFrequency': 3580}}]
      
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3580}      
      self.assertChannelsContainFrequencyRange(channels, frequency_range)
    
   @unittest.expectedFailure
   def test_assertChannelsContainFrequencyRangeShouldFaileWhenChannelLowerThanRange(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3545, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3560, 'highFrequency': 3570}}, 
                   {'frequencyRange' : {'lowFrequency': 3570, 'highFrequency': 3575}}]
       
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}      
      self.assertChannelsContainFrequencyRange(channels, frequency_range)
      
   @unittest.expectedFailure
   def test_assertChannelsContainFrequencyRangeShouldFaileWhenChannelHigherThanRange(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3560, 'highFrequency': 3570}}, 
                   {'frequencyRange' : {'lowFrequency': 3570, 'highFrequency': 3580}}]
       
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}     
      self.assertChannelsContainFrequencyRange(channels, frequency_range)

   @unittest.expectedFailure
   def test_assertChannelsContainFrequencyRangeShouldFaileWhenMissingChannel(self):
      channels = [{'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3560}},
                   {'frequencyRange' : {'lowFrequency': 3570, 'highFrequency': 3575}}, 
                   {'frequencyRange' : {'lowFrequency': 3550, 'highFrequency': 3565}}]
       
      frequency_range = { 'lowFrequency': 3550, 'highFrequency': 3575}
       
      self.assertChannelsContainFrequencyRange(channels, frequency_range)
