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

"""A SAS-TH HTTP Server implementation, based on v1.2 of the SAS-SAS TS.

A SAS-TH test server could be run by creating the object for the class SasTestHarnessServer
and by invoking the API start()".
"""

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
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

CERT_FILE = 'certs/server.cert'
KEY_FILE = 'certs/server.key'
CA_CERT = 'certs/ca.cert'
CIPHERS = [
    'AES128-GCM-SHA256',              # TLS_RSA_WITH_AES_128_GCM_SHA256
    'AES256-GCM-SHA384',              # TLS_RSA_WITH_AES_256_GCM_SHA384
    'ECDHE-ECDSA-AES128-GCM-SHA256',  # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    'ECDHE-ECDSA-AES256-GCM-SHA384',  # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    'ECDHE-RSA-AES128-GCM-SHA256',    # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
]


class SasTestHarnessServer(threading.Thread):
  """
  Test Harness acting as a HTTP Server running in background and serving Pull/GET requests.
  """
  def __init__(self, name, base_url, dump_path, cert_file=None, key_file=None):
    """ This constructor initializes the SasTestHarnessServer class with required information
    passed as args

    Args:
        name: A name for SAS-TH.If multiple SAS-THs are created then this value should be unique.
        base_url: base url of SAS-TH that the SAS UUT should connect to for FAD records.
        dump_path: file_path where the FAD records served by the SAS-TH will be placed.
        cert_file: The certificate used by SAS-TH to authorize with SAS UUT.
        key_file:  The private key file for the cert_file.
    """
    super(SasTestHarnessServer, self).__init__()
    self.name = name
    self.http_server_url = base_url
    self.dump_path = os.path.join(name, dump_path)
    self.cert_file = cert_file if cert_file is not None else CERT_FILE
    self.key_file = key_file if key_file is not None else KEY_FILE
    self.daemon = True
    self.server = None


  def getSasThUrl(self):
    return self.http_server_url

  def getUrlHostNameAndPort(self):
    """ This method will return the http_server_url used in startServer method by truncating other
    querystring in url and returns tuple(<hostname>, <port>)
    """
    splitted_url = self.http_server_url.split('/')[2:]
    logging.info(splitted_url)
    return splitted_url[0].split(':')[0], int(splitted_url[0].split(':')[1])

  def getDumpFilePath(self):
    """ This method will return absolute path where FAD Records of SAS-TH are stored.
    """
    harness_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    dumpfile_path = os.path.join(harness_dir, 'FADRecords', self.dump_path)
    return dumpfile_path

  def run(self):
    self.startServer()

  def shutdown(self):
    self.stopServer()

  def startServer(self):
    """ Starts the HTTPServer as background thread.
    """
    SasTestHarnessServerHandler.setupDumpFilePath(self.getDumpFilePath())
    self.server = HTTPServer(self.getUrlHostNameAndPort(), SasTestHarnessServerHandler)
    self.server.socket = ssl.wrap_socket(
        self.server.socket,
        certfile=self.cert_file,
        keyfile=self.key_file,
        ca_certs=CA_CERT,
        cert_reqs=ssl.CERT_REQUIRED,
        ssl_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=':'.join(CIPHERS),
        server_side=True
        )
    # Start HTTP Server
    logging.info("Started Test Harness Server:%s at %s", self.name, self.http_server_url)
    self.server.serve_forever()

  def stopServer(self):
    """ This method used to stop http_server  """
    self.server.shutdown()
    logging.info("Stopped Test Harness Server:%s", self.name)

  def generateFadRecords(self, cbsd_records, grant_records_list, ppa_records,
                         esc_sensor_records):
    """ Generates the cbsd,ppa and esc_sensor dump file and dumps the FAD file in specified path

    Args:
       cbsd_records: list of cbsdData objects that includes one or more grants object and FAD
       grant_records_list: list of muliple grant records for all cbsd devices
         For an example : muliple grants [ [grant1, grant2], [grant1, grant2] ] associated with each
         cbsd records [ cbsd1, cbsd2 ]
       ppa_records:  list of ppa_record objects used to generate ppa_dump file and FAD
       esc_sensor_records: list of esc_sensor_records objects used to generate
                            esc_sensor_records and FAD

    Returns:
       It returns None and successfully generates the dumps in specified file path
    """

    def getCbsdReferenceId(fcc_id, serial_number):
      """creates encoded cbsd_reference_id using sha1 with fcc_id and serial number of cbsd
      """
      return str(fcc_id + '/' + str(hashlib.sha1(serial_number).hexdigest())).encode('utf-8')

    def writeDumpFile(file_path, data):
      """ Write JSON data to specified file """
      file_handler = open(file_path, "w")
      file_handler.writelines(json.dumps(data, sort_keys=True, indent=4))
      file_handler.close()

    def cleanDumpFiles():
      """ Clean existing dumpfile if any """
      map(os.remove, (os.path.join(self.getDumpFilePath(), file)
                      for file in os.listdir(self.getDumpFilePath())))

    def createFadRecord(url, record):
      """ Creates the files object that includes url,checksum,size,version and recordtype of record
          required to be packed in FAD
      """
      fad_record = {}
      fad_record['url'] = url
      fad_record['checksum'] = hashlib.sha1(json.dumps(record)).hexdigest()
      fad_record['size'] = sys.getsizeof(record)
      fad_record['version'] = self.getSasThUrl().split('/')[-1]
      if 'cbsd' in url:
        fad_record['recordType'] = "cbsd"
      elif 'zone' in url:
        fad_record['recordType'] = "zone"
      elif 'esc_sensor' in url:
        fad_record['recordType'] = "esc_sensor"
      else:
        pass
      return fad_record

    def createFadObject(all_activity_dump):
      """Creates the FAD object format and embed the active dump file object of different recordtype
      """
      full_activity_dump = {}
      full_activity_dump['files'] = all_activity_dump
      end_time = datetime.now()
      end_time = time.strftime(end_time.replace(microsecond=0).isoformat()) + 'Z'
      full_activity_dump['generationDateTime'] = end_time
      full_activity_dump['description'] = 'Load {} FAD to SAS UUT'.format(self.name)
      return full_activity_dump

    fad_record_list = []

    # Before Generate FAD record cleanup if any dump file
    logging.debug('Clean dump files if any exist already')
    cleanDumpFiles()
    for index, (cbsd_record, grant_records) in enumerate(zip(cbsd_records, grant_records_list)):
      encoded_cbsd_id = getCbsdReferenceId(cbsd_record['fccId'],
                                           cbsd_record['cbsdSerialNumber'])
      # Calculate grant_expiry time for grant objects if grant expiry time may
      # be incorrect or missing
      grant_expiry_time = datetime.now().today() + timedelta(hours=24)
      grant_expiry_time = time.strftime(grant_expiry_time.replace(microsecond=0).isoformat()) + 'Z'

      internal_data = {
          'id': 'cbsd/{}'.format(encoded_cbsd_id),
          'registration': {
              'fccId': cbsd_record['fccId'],
              'cbsdCategory': cbsd_record['cbsdCategory'],
              'callSign': cbsd_record['callSign'],
              'userId': cbsd_record['userId'],
              'airInterface': cbsd_record['airInterface'],
              'measCapability': cbsd_record['measCapability'],
              'installationParam': cbsd_record['installationParam']
          }
      }
      # Check if groupingParam in CBSDRecord and add it by default
      if internal_data['registration'].has_key('groupingParam'):
        internal_data['registration'].update({'groupingParam': cbsd_record['groupingParam']})
      internal_data_grant = {}
      internal_data_grant['grants'] = []
      # Read all grant records if mulitiple grant records assciated with single cbsd
      for grant_record in grant_records:
        grant_data = {}
        if not grant_record.has_key('id'):
          grant_data['id'] = 'SAMPLE_ID_{:05}'.format(random.randrange(1, 10 ** 5))
        else:
          grant_data['id'] = grant_record['id']
        grant_data['operationParam'] = grant_record['operationParam']
        if not grant_record.has_key('channelType'):
          grant_data['channelType'] = 'GAA'
        else:
          grant_data['channelType'] = grant_record['channelType']
        if not grant_record.has_key('grantExpireTime'):
          grant_data['grantExpireTime'] = grant_expiry_time
        else:
          grant_data['grantExpireTime'] = grant_record['grantExpireTime']
        if not grant_record.has_key('terminated'):
          grant_data['terminated'] = False
        else:
          grant_data['terminated'] = grant_record['terminated']
        internal_data_grant['grants'].append(grant_data)
      internal_data.update(internal_data_grant)
      generated_file_name = '{}.json'.format(encoded_cbsd_id.decode('utf-8').split('/')[-1])
      cbsd_dump_file_path = os.path.join(self.getDumpFilePath(), generated_file_name)
      writeDumpFile(cbsd_dump_file_path, internal_data)
      cbsd_url = self.getSasThUrl() + '/cbsd/%s' % quote(encoded_cbsd_id)
      fad_record_cbsd = createFadRecord(cbsd_url, internal_data)
      fad_record_list.append(fad_record_cbsd)

    for ppa_record in ppa_records:
      generated_file_name = '{}.json'.format(ppa_record['id']).split('/')[-1]
      ppa_record_dump_file_path = os.path.join(self.getDumpFilePath(), generated_file_name)
      # Check cbsdReferenceID in ppaInfo and add cbsdReferenceID if not present
      if not ppa_record['ppaInfo'].has_key('cbsdReferenceId'):
         ppa_record['ppaInfo'].update({'cbsdReferenceId': ['cbsdId-1', 'cbsdId-2']})
      writeDumpFile(ppa_record_dump_file_path, ppa_record)
      ppa_record_url = self.getSasThUrl() + '/' + ppa_record['id']
      fad_record_ppa = createFadRecord(ppa_record_url, ppa_record)
      fad_record_list.append(fad_record_ppa)

    for esc_sensor_record in esc_sensor_records:
      #generated_file_name = '{}.json'.format(esc_sensor_record['id'].split('/')[-1])
      generated_file_name = '{}.json'.format(str(hashlib.sha1(esc_sensor_record['id']).hexdigest()).encode('utf-8'))
      esc_sensor_record_dump_file_path = os.path.join(self.getDumpFilePath(), generated_file_name)
      writeDumpFile(esc_sensor_record_dump_file_path, esc_sensor_record)
      esc_sensor_record_url = self.getSasThUrl() + '/%s/%s' \
                                                      % (esc_sensor_record['id'], generated_file_name)
      fad_record_esc = createFadRecord(esc_sensor_record_url, esc_sensor_record)
      fad_record_list.append(fad_record_esc)

    fad_file_path = os.path.join(self.getDumpFilePath(), 'FAD.json')
    full_activity_dump = createFadObject(fad_record_list)
    writeDumpFile(fad_file_path, full_activity_dump)
    logging.info("FAD Records generated successfully.The files are placed "
                 "under the path:%s", self.getDumpFilePath())


class SasTestHarnessServerHandler(BaseHTTPRequestHandler):
  """SasTestHarnessServerHandler class is inherited with BaseHTTPRequestHandler
  to serve HTTP Response
  """
  @classmethod
  def setupDumpFilePath(cls, file_path):
    """Setup the absolute path of dumpfile used in do_GET() method """
    cls.__dumpfile_path = file_path
    if not os.path.exists(cls.__dumpfile_path):
      os.makedirs(cls.__dumpfile_path, 0755)
    cls.__fadfile_path = os.path.join(cls.__dumpfile_path, 'FAD.json')

  def do_GET(self):
    """Handles Pull/GET Request and returns Path of the Request to callback Method"""

    def checkDumpFileExist(url_id):
      """vCheck the url_id received in GET request passed as argument to check corresponding
      dump file exist in that path
      """
      return os.path.exists(os.path.join(self.__dumpfile_path, '{}.json'.format(url_id)))

    def getDumpFilePath(url_id):
      """ Return the absolute path of FAD records that are going
      to be generated
      """
      return os.path.join(self.__dumpfile_path, '{}.json'.format(url_id))

    if "dump" in self.path:
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.load(open(os.path.join(self.__fadfile_path))))
    else:
      url_encoded_id = self.path.split('/')[-1]
      self.log_message(url_encoded_id)
      if not checkDumpFileExist(url_encoded_id):
        self.send_error(404)
        return
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.load(open(getDumpFilePath(url_encoded_id))))
