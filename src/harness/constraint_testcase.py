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

import json
from datetime import datetime,timedelta
import logging
import os
import time
import sys
import sas
import sas_testcase
from sas_test_harness import SasTestHarness, GetSasTestHarnessUrl

class ConstraintTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    # Note that we disable the admin.Reset(), to avoid 'unexpected' request
    # to SAS UUT before a test really starts.
    # Tests changing the SAS UUT state must explicitly call the SasReset()
    #self.SasReset()
    self.sasTHInstances = {}

  def SasReset(self):
    self._sas_admin.Reset()

  def tearDown(self):
     # check if any SASTH is started and try to stop it
     for sasTH in sorted(self.sasTHInstances.itervalues()):
         sasTH.shutdown()

  def createSASTH(self,sasTHConfig):
     sasTHSettings = sasTHConfig['sas_hareness']
     # prepare a HTTPServer Object for each sasTH mentioned in configuration file
     for item in sasTHSettings:
        sasTHServer = SasTestHarness(name=item['name'],url=item['url'],
                                     cert_file=item['cert_file'],key_file=item['key_file'])
        self.sasTHInstances[item['name']] = sasTHServer

  def configureFADForEachSASTH(self,iterationNumber):
     '''
     This method used to configure FAD record for each SAS-TH that includes CBSDactivity based on configuration files
     and start SAS-TH Http Server instance with configurable host_name and port and ready to serve for Pull Dump request from
     SAS UUT/Main Test Hareness
     SAS-TH Http Server will be started automatically as background thread and alive till end of Main Thread/Main Test Hareness
     SAS-TH Http Server will be stopped automatically during teardown of tests if any
     :param configDir:
     :return: None
     '''
     def getTimeStamp():
       '''
       helper method used to calculate start/end/grant time to populate in FAD records
       :returns start_time,end_time,grant_expire_time
       '''
       end_time = datetime.now()
       time_delta = timedelta(hours=-24)
       start_time = end_time.today() + time_delta
       end_time = str(end_time.replace(microsecond=0).isoformat()) + 'Z'
       start_time = str(start_time.replace(microsecond=0).isoformat()) + 'Z'
       time_delta1 = timedelta(hours=24)
       grant_expire = datetime.now().today() + time_delta1
       grant_expire = str(grant_expire.replace(microsecond=0).isoformat()) + 'Z'
       return (start_time,end_time,grant_expire)
    
     configDir = 'configs/test_WINNF_FT_S_MCP_1' 
     for sasTHName,sasTHInstance in sorted(self.sasTHInstances.items()):
        startTime,endTime,grant_expire = getTimeStamp()
        # load dumpfile which starts with SAS-TH name to identify easily specfic CBSD dump record associated with corresponding SAS-TH
        sasTHName = sasTHName + '-' + iterationNumber
        dumpfiles = [dumpfile for dumpfile in os.listdir(configDir)
                         if dumpfile.startswith(sasTHName)]
        full_activity_dump = {}
        all_activity_dump_list = []
        for dumpfile in dumpfiles:
          internal_data = json.load(open(os.path.join(configDir,dumpfile)))
          for field,data in internal_data.items():
              if data.has_key('recordData'):
                  urlId = data['recordData'][0]['id']
                  grantsList = data['recordData'][0]['grants']
                  for index in range(len(grantsList)):
                    grantsList[index]['grantExpireTime'] = grant_expire
              if data.has_key('startTime'):
                data['startTime'] = startTime
              if data.has_key('endTime'):
                data['endTime'] = endTime

          # generate cbsdActivity for cbsdrecords for sasTH
          sasTHInstance.setupCbsdActivity(urlId, internal_data)
          logging.debug("Generated CBSDActivity Dump at "+sasTHName+" as follows\n")
          logging.debug(json.dumps(sasTHInstance.parameters['cbsdActivity'], sort_keys=True, indent=4,
                                  separators=(',', ': ')))

          activity_dump_file = {}
          # create a FAD that contains cbsdrecords and tag with unique url have cbsdId
          activity_dump_file['url'] = 'https://' + sasTHInstance.url[0]+':'+str(sasTHInstance.url[1]) + '/cbsd/%s' % urlId
          activity_dump_file['checksum'] = "For the future calculating"
          activity_dump_file['size'] = sys.getsizeof(internal_data)
          activity_dump_file['version'] = "v1.2"
          activity_dump_file['recordType'] = "cbsd"
          all_activity_dump_list.append(activity_dump_file)

        full_activity_dump['files'] = all_activity_dump_list
        full_activity_dump['generationDateTime'] = endTime
        full_activity_dump['description'] = 'Load {} FAD to SAS UUT'.format(sasTHName)

        # Setup the Full Activity response for SAS Under Test
        sasTHInstance.setupFullActivity(full_activity_dump)
        # Start SAS-TH HttpServer on specified port and ready to give push dump response
        sasTHInstance.start()
        time.sleep(30)
        logging.info("%s is running with %s as Background Thread now" %(sasTHInstance.name,sasTHInstance.url))
        logging.debug("Generated FAD at " + sasTHName + " as follows\n")
        logging.debug(json.dumps(sasTHInstance.parameters['fullActivity'], sort_keys=True, indent=4,
                                separators=(',', ': ')))
