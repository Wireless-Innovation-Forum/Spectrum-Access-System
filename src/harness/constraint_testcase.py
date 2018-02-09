#    Copyright 2018 SAS Project Authors. All Rights Reserved.
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

  def tearDown(self):
     # check if any SASTH is started and try to stop it
     for sas_th in self.sas_th_harness.itervalues():
         sas_th.shutdown()

  def create_sas_th(self,sas_th_config):
     self.sas_th_harness = {}
     sas_th_settings = sas_th_config['sasHarness']
     # prepare a HTTPServer Object for each sasTH mentioned in configuration file
     for sas in sas_th_settings:
         sas_th_server = SasTestHarness(name=sas['name'],url=sas['url'],
                                     cert_file=sas['cert_file'],key_file=sas['key_file'])
         self.sas_th_harness[sas['name']] = sas_th_server

  def configure_fad_for_each_sas_th(self,iteration_number):
     """
     This method used to configure FAD record for each SAS-TH that includes CBSDactivity based on configuration files
     and start SAS-TH Http Server instance with configurable host_name and port and ready to serve for Pull Dump request from
     SAS UUT/Main Test Hareness
     SAS-TH Http Server will be started automatically as background thread and alive till end of Main Thread/Main Test Hareness
     SAS-TH Http Server will be stopped automatically during teardown of tests if any
     :param iteration_number
     :return: None
     """
     def get_time_stamp():
       """
       helper method used to calculate start/end/grant time to populate in FAD records
       :returns start_time,end_time,grant_expire_time
       """
       end_time = datetime.now()
       start_time = end_time.today() + timedelta(hours=-24)
       end_time = time.strftime(end_time.replace(microsecond=0).isoformat()) + 'Z'
       start_time = time.strftime(start_time.replace(microsecond=0).isoformat()) + 'Z'
       grant_expire = datetime.now().today() + timedelta(hours=24)
       grant_expire = str(grant_expire.replace(microsecond=0).isoformat()) + 'Z'
       return (start_time,end_time,grant_expire)
     for sas_th_name,sas_th_instance in self.sas_th_harness.items():
        start_time,end_time,grant_expire = get_time_stamp()
        # Load cbsd dump as per the iteration in the configuration
        sas_cbsd_fad_object = sas_th_instance['fad_record'][iteration_number]['cbsd']
        full_activity_dump = {}
        all_activity_dump_list = []


        #Initialize startTime, endTime and grantExpireTime for each cbsd record
        for field,data in sas_cbsd_fad_object.items():
              if data.has_key('recordData'):
                  url_id = data['recordData'][0]['id']
                  grants_list = data['recordData'][0]['grants']
                  for index in range(len(grantsList)):
                    grants_list[index]['grantExpireTime'] = grant_expire
              if data.has_key('startTime'):
                data['startTime'] = startTime
              if data.has_key('endTime'):
                data['endTime'] = endTime

        # generate cbsdActivity for cbsdrecords for sas_th
        sas_th_instance.setup_cbsd_activity(url_id, internal_data)
        logging.debug("Generated CBSDActivity Dump at "+sas_th_instance.parameters['cbsdActivity']+" as follows\n")
        logging.debug(json.dumps(sas_th_instance.parameters['cbsdActivity'], sort_keys=True, indent=4,
                                separators=(',', ': ')))

        activity_dump_file = {}
        # create a FAD that contains cbsdrecords and tag with unique url have cbsdId
        activity_dump_file['url'] = 'https://' + sas_th_instance.url[0]+':'+str(sas_th_instance.url[1]) + '/cbsd/%s' % url_id
        activity_dump_file['checksum'] = "For the future calculating"
        activity_dump_file['size'] = sys.getsizeof(internal_data)
        activity_dump_file['version'] = "v1.2"
        activity_dump_file['recordType'] = "cbsd"
        all_activity_dump_list.append(activity_dump_file)

        full_activity_dump['files'] = all_activity_dump_list
        full_activity_dump['generationDateTime'] = endTime
        full_activity_dump['description'] = 'Load {} FAD to SAS UUT'.format(sasTHName)

        # Setup the Full Activity response for SAS Under Test
        sas_th_instance.setup_full_activity(full_activity_dump)
        # Start SAS-TH HttpServer on specified port and ready to give push dump response
        sas_th_instance.start()
        time.sleep(30)
        logging.info("%s is running with %s as Background Thread now" %(sas_th_instance.name,sas_th_instance.url))
        logging.debug("Generated FAD at " + sasTHName + " as follows\n")
        logging.debug(json.dumps(sas_th_instance.parameters['fullActivity'], sort_keys=True, indent=4,
                                separators=(',', ': ')))
