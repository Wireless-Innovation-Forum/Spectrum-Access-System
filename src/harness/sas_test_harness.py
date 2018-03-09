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

""" A SAS Test Harness HTTP Server implementation based on v1.2 of the SAS-SAS TS.
A SAS Test Harness server could be run by creating the object for the class SasTestHarnessServer
and by invoking the API start().
"""

import ConfigParser
import hashlib
import inspect
import json
import logging
import os.path
import random
import ssl
import sys
import threading
import time
from datetime import datetime, timedelta
from urllib import quote
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

DEFAULT_CERT_FILE = 'certs/server.cert'
DEFAULT_KEY_FILE = 'certs/server.key'
DEFAULT_CA_CERT = 'certs/ca.cert'
CIPHERS = [
    'AES128-GCM-SHA256',              # TLS_RSA_WITH_AES_128_GCM_SHA256
    'AES256-GCM-SHA384',              # TLS_RSA_WITH_AES_256_GCM_SHA384
    'ECDHE-ECDSA-AES128-GCM-SHA256',  # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    'ECDHE-ECDSA-AES256-GCM-SHA384',  # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    'ECDHE-RSA-AES128-GCM-SHA256',    # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
]

class SasTestHarnessServer(threading.Thread):
  """
  SAS Test Harness class to create FAD records and to create a HTTP server
  to serve the FAD records.This class inherits from the Python Thread class.
  Every instance created for this class can be run under a separate thread. The
  code to be executed by the thread is placed under the overridden method run ()
  where a HTTP server is created to serves the FAD files.
  """
  def __init__(self, name, host_name, port, cert_file=None,
               key_file=None, ca_cert_file=None):
    """ This constructor initializes the SasTestHarnessServer class with required information
    passed as args.

    Args:
        name: A name for SAS Test Harness.If multiple SAS Test Harnesses are created
              then this value should be unique.
        host_name: Host name part of the SAS Test Harness URL.
                   Note: this is without https:// or port number or version.
        port: port of SAS Test Harness host where http server is configured.
        cert_file: The relative path from the execution directory to the certificate
                   file used by SAS Test Harness to authorize with SAS UUT.
        key_file: The relative path from the execution directory to the private key file
                  for the cert_file.
        ca_cert_file: The relative path from the execution directory to the trusted
                  CA certificate chain.
    """
    super(SasTestHarnessServer, self).__init__()
    self.name = name
    self.host_name = host_name
    self.port = port
    self.sas_version = self.getSasTestHarnessVersion()

    #BaseURL format should be https: // < hostname >: < port > / versionX.Y
    self.http_server_url = "https://" + host_name + ':' + str(port) + '/' + self.sas_version
    self.dump_path = self.__generateTempDirectory()
    self.cert_file = cert_file if cert_file is not None else DEFAULT_CERT_FILE
    self.key_file = key_file if key_file is not None else DEFAULT_KEY_FILE
    self.ca_cert_file = ca_cert_file if ca_cert_file is not None else DEFAULT_CA_CERT
    self.server = None
    self.setDaemon(True)

  def __del__(self):
    self.cleanDumpFiles()

  def __generateTempDirectory(self):
    """ This method will generate a random directory using the current timestamp.
    The relative path of the directory is ./SAS-Test-Harness-Data/YYYY-MM-DD-HH-MM-SS-mmmmmm.

    Returns: Returns the absolute path of the created temporary directory.
    """
    sas_test_harness_data_dir = os.path.join(os.path.dirname(os.path.abspath(
      inspect.getfile(inspect.currentframe()))), 'SAS-Test-Harness-Data')
    current_time_stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
    temp_dump_dir_path = os.path.join(sas_test_harness_data_dir, current_time_stamp)
    os.makedirs(temp_dump_dir_path)

    return temp_dump_dir_path

  def getSasTestHarnessVersion(self):
    """This method retrieves the SAS Test Harness Version from sas.cfg.
    Returns: Returns SAS version of the SAS Test Harness to be used
             to construct the base URL.
    """
    config_parser = ConfigParser.RawConfigParser()
    config_parser.read(['sas.cfg'])
    sas_harness_version = config_parser.get('SasConfig', 'Version')
    return sas_harness_version

  def getBaseUrl(self):
    return self.http_server_url

  def getDumpFilePath(self):
    return self.dump_path

  def run(self):
    """ Starts the HTTPServer as background thread.
    The run() method is an overridden method from thread class and it gets invoked
    when the thread is started using thread.start().
    """
    self.server = SasHttpServer(self.dump_path,
                                (self.host_name, self.port),
                                SasTestHarnessServerHandler)
    self.server.socket = ssl.wrap_socket(
        self.server.socket,
        certfile=self.cert_file,
        keyfile=self.key_file,
        ca_certs=self.ca_cert_file,
        cert_reqs=ssl.CERT_REQUIRED,
        ssl_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=':'.join(CIPHERS),
        server_side=True
    )

    # Start HTTP Server.
    logging.info("Started Test Harness Server:%s at %s", self.name, self.http_server_url)
    self.server.serve_forever()

  def shutdown(self):
    """ This method is used to stop HTTPServer Socket
    """
    self.server.shutdown()
    logging.info("Stopped Test Harness Server:%s", self.name)


  def cleanDumpFiles(self):
    """ Clean existing dumpfile if any. """
    temp_dir_path = self.getDumpFilePath()
    map(os.remove, (os.path.join(temp_dir_path, file_path)
                    for file_path in os.listdir(temp_dir_path)
                    if os.path.exists(os.path.join(temp_dir_path, file_path))))
    os.rmdir(temp_dir_path)
    logging.info('all dump records generated by this testcase are cleaned successfully')
    
  def __createFadObject(self, all_activity_dump):
    """Creates the FAD object format and embed the active dump file object of different recordtype.
    """
    full_activity_dump = {}
    full_activity_dump['files'] = all_activity_dump
    end_time = time.strftime(datetime.now().replace(microsecond=0).isoformat()) + 'Z'
    full_activity_dump['generationDateTime'] = end_time
    full_activity_dump['description'] = 'Load {} FAD to SAS UUT'.format(self.host_name)
    return full_activity_dump

  def __createFadRecord(self, encoded_url, record):
    """ Creates the files object that includes url,checksum,size,version and recordtype of record
        required to be packed in FAD.
    """
    fad_record = {}
    fad_record['url'] = encoded_url
    fad_record['checksum'] = hashlib.sha1(json.dumps(record)).hexdigest()
    fad_record['size'] = sys.getsizeof(record)
    fad_record['version'] = self.sas_version
    if 'cbsd' in encoded_url:
      fad_record['recordType'] = "cbsd"
    elif 'zone' in encoded_url:
      fad_record['recordType'] = "zone"
    elif 'esc_sensor' in encoded_url:
      fad_record['recordType'] = "esc_sensor"
    else:
      raise Exception("ConfigurationError:: Incorrect Record Type received in URL:{}".format(encoded_url))
    return fad_record

  def __writeDumpFile(self, file_name, data):
    """ Write JSON data to specified file. """
    dump_file_path = os.path.join(self.getDumpFilePath(), file_name)
    with open(dump_file_path, "w") as file_handler:
      file_handler.writelines(json.dumps(data, sort_keys=True, indent=4))

  def __verifyRecords(self, dump_records_list):
    """This method checks if given dump records [cbsd1,..,cbsdN] or 
       [pp1,..,ppaN] or [esc1,..,escN] is grouped with same record type 
       by using id field.
    Args:
       dump_records_list: List of dump_records object. Contains dump records 
                        in the format of [[cbsd1,..,cbsdn],[cbsda,..,cbsdc],
                        [pp1,..,ppa3],[esc1,..,esc3]]"""

    for index, dump_records in enumerate(dump_records_list):
        if len(dump_records) == 0:
           raise Exception("ConfigurationError:No records are configured")

        if not dump_records[0].has_key('id'):
           raise Exception("ConfigurationError:Id field is not configured")
        
        if 'cbsd' in dump_records[0]['id']:
            if any('cbsd' not in cbsd_dump['id'] for cbsd_dump in dump_records):
               raise Exception("ConfigurationError:CBSD dump records are not of same type")
        elif 'zone' in dump_records[0]['id']:
              if any('zone' not in zone_dump['id'] for zone_dump in dump_records):
                 raise Exception("ConfigurationError:Zone dump records are not of same type")
        elif 'esc_sensor' in dump_records[0]['id']:
              if any('esc_sensor' not in esc_dump['id'] for esc_dump in dump_records):
                 raise Exception("ConfigurationError:ESC dump records are not of same type")
        else:
            raise Exception("ConfigurationError:incorrect record type. \
                                           Unable to write FAD record")

  def writeFadRecords(self, dump_records_list):
    """This method is used to write dump records in specified path. 
       These files will be served by SAS Test Harness.
    Args:
       dump_records_list: List of dump_records object required to 
            be written on the dump path. Contains dump records in the format of 
            [[cbsd1,..,cbsdn],[cbsda,..,cbsdc],[pp1,..,ppa3],[esc1,..,esc3]]
            In this case four dump files will be created 
            activity_dump_file_cbsd0.json - contains 1-n cbsd records
            activity_dump_file_cbsd1.json - contains a-c cbsd records
            activity_dump_file_zone2.json - contains 1-3 ppa records
            activity_dump_file_esc_sensor3.json - contains 1-3 esc records

    Returns:
       It returns None and all records are dumped in specified path."""
    
    fad_record_list = []

    self.__verifyRecords(dump_records_list)

    for index, dump_records in enumerate(dump_records_list):
        if 'cbsd' in dump_records[0]['id']:
           generated_file_name = 'activity_dump_file_cbsd'+str(index)+'.json'
           record_url = self.getBaseUrl() +'/cbsd/'+ generated_file_name
        elif 'zone' in dump_records[0]['id']:
            generated_file_name = 'activity_dump_file_zone'+str(index)+'.json'
            record_url = self.getBaseUrl() +'/zone/'+ generated_file_name
        elif 'esc_sensor' in dump_records[0]['id']:
            generated_file_name = 'activity_dump_file_esc_sensor'+str(index)+'.json'
            record_url = self.getBaseUrl() +'/esc_sensor/'+ generated_file_name
        else:
            raise Exception("ConfigurationError:incorrect record type. \
                                           Unable to write FAD record")
        # creates the dump file containing records of the same type
        self.__writeDumpFile(generated_file_name, dump_records)
        fad_record = self.__createFadRecord(record_url, dump_records)
        fad_record_list.append(fad_record)
    
    # create full activity dump file
    fad_file_name = 'FAD.json'
    full_activity_dump = self.__createFadObject(fad_record_list)
    self.__writeDumpFile(fad_file_name, full_activity_dump)
    logging.info("FAD Records generated successfully."
                    "The files are placed under the path:%s", self.getDumpFilePath())


class SasHttpServer(HTTPServer):
  """ The class SasHttpServer overrides built-in HTTPServer and takes the
  parameter base_path used to serve the files. This is needed to have SAS
  test harnesses to server files from different directories.
  """
  def __init__(self, base_path, server_address, RequestHandlerClass):
    self.base_path = base_path
    HTTPServer.__init__(self, server_address, RequestHandlerClass)

class SasTestHarnessServerHandler(BaseHTTPRequestHandler):
  """SasTestHarnessServerHandler class is inherited with BaseHTTPRequestHandler
  to serve HTTP Response.
  """

  def __checkDumpFileExist(self, url_id):
    """Check the url_id received in GET request passed as argument to check corresponding
    dump file exist in that path.
    """
    return os.path.exists(os.path.join(self.server.base_path, '{}.json'.format(url_id)))

  def __getDumpFilePath(self, url_id):
    """ Return the absolute path of FAD records that are going
    to be generated.
    """
    return os.path.join(self.server.base_path, '{}.json'.format(url_id))

  def do_GET(self):
    """Handles Pull/GET Request and returns Path of the Request to callback Method."""

    if "dump" in self.path:
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.load(open(self.__getDumpFilePath('FAD'))))
    else:
      url_encoded_id = self.path.split('/')[-1]
      if not self.__checkDumpFileExist(url_encoded_id):
        self.send_error(404)
        return
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.load(open(self.__getDumpFilePath(url_encoded_id))))

# Helper functions for FAD related tests.
def generateCbsdReferenceId(fcc_id, serial_number):
  """creates encoded cbsd_reference_id using sha1 with fcc_id and serial number of cbsd.
  """
  return str("cbsd/" + fcc_id + '/' + str(hashlib.sha1(serial_number).hexdigest())).encode('utf-8')

def generateCbsdRecords(registration_requests, grant_requests_list):
  """ Generates the cbsdData Object by combining registration request 
      and grant request based on SAS-SAS TS.
  Args:
     registration_requests: List of CBSD registration requests. Corresponding 
                            CBSDs will have at least one corresponding Grant request
     grant_requests_list:   List of muliple grant requests for all cbsd devices.
                            For an example : muliple grants [ [grant1, grant2], 
                            [grant3, grant4 ] are associated with each cbsd records
                            [ cbsd1, cbsd2 ].

  Returns:
     It returns list of CbsdData object based on SAS-SAS TS.
  """

  cbsd_records_list = []
  if not len(registration_requests) == len(grant_requests_list):
    raise Exception('ConfigurationError: Number of registration requests does' 
                     ' not match with number of grant requests')

  if any(len(grant_requests) == 0 for grant_requests in grant_requests_list):
     raise Exception('ConfigurationError: At least one of the grant request list is empty')

  for index, (registration_request, grant_requests) in enumerate \
                       (zip(registration_requests, grant_requests_list)):
    cbsd_reference_id = generateCbsdReferenceId(registration_request['fccId'],
                                   registration_request['cbsdSerialNumber'])

    internal_data = {
        'id': cbsd_reference_id,
        'registration': {
            'fccId': registration_request['fccId'],
            'cbsdCategory': registration_request['cbsdCategory'],
            'callSign': registration_request['callSign'],
            'airInterface': registration_request['airInterface'],
            'measCapability': registration_request['measCapability'],
            'installationParam': registration_request['installationParam']
        }
    }

    # Check if groupingParam optional parameter present in CBSDRecord then
    # add to registration object.
    if registration_request.has_key('groupingParam'):
      internal_data['registration'].update({'groupingParam': 
                         registration_request['groupingParam']})

    internal_data['grants'] = []

    # Read all grant records if mulitiple grant records are associated with 
    # single cbsd.
    for grant_request in grant_requests:
      grant_data = {}

      # Auto-generating GrantData 'id' field.
      grant_data['id'] = 'SAMPLE_ID_{:05}'.format(random.randrange(1, 10 ** 5))

      assert grant_request.has_key('operationParam'), "operationParam does not exist in GrantRequest"
      grant_data['operationParam'] = grant_request['operationParam']

      # requestedOperationParam is a required field in SAS-SAS exchange in Release 1.
      # Copying the operationParam into requestedOperationParam
      grant_data['requestedOperationParam'] = grant_request['operationParam']

      # Channel type is mandatory in GrantData Object.
      # Setting it to 'GAA' by default.
      grant_data['channelType'] = 'GAA'

      # Assign grant_expire_time to grant objects.
      grant_time_stamp = datetime.now().today() + timedelta(days=2*365)
      grant_expire_time = time.strftime(grant_time_stamp.\
                              replace(microsecond=0).isoformat()) + 'Z'

      # grantExpireTime is mandatory in GrantData Object.
      # Setting it to a value of 24 hours from now.
      grant_data['grantExpireTime'] = grant_expire_time

      #  'terminated' field is set to 'False' by default.
      grant_data['terminated'] = False

      internal_data['grants'].append(grant_data)

    cbsd_records_list.append(internal_data)
   
  return cbsd_records_list

def generatePpaRecords(ppa_records, cbsd_reference_ids):
  """ Generates the ppaData by adding cbsd_reference_id list to ppa_info 
      based on SAS-SAS TS.

  Args:
     ppa_records:        List of ppa_record objects used to generate ppa_dump file.
     cbsd_reference_ids: List of lists containing one or more CBSD Reference 
                         IDs in the cluster for each PPA record. 
  Returns:
     It returns list of ppa_records based on SAS-SAS TS.
  """

  ppa_records_list = []
  for ppa_record, cbsd_reference_id in \
              zip(ppa_records, cbsd_reference_ids):

    # Check cbsdReferenceID in ppaInfo and add cbsdReferenceID if not present.
    if not ppa_record['ppaInfo'].has_key('cbsdReferenceId'):
      ppa_record['ppaInfo'].update({'cbsdReferenceId': cbsd_reference_id})
    ppa_records_list.append(ppa_record)

  return ppa_records_list
