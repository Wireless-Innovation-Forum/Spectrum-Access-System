import ssl
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import sas_test_harness_server_interface
import logging
import json
import os
import ConfigParser
from sas import _RequestGet, _RequestPost, TlsConfig
from sas_objects import FullActivityDumpObject, DomainProxyObject, Cbsd

PORT = 9001
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


def GetSasTestHarnessUrl():
  config_parser = ConfigParser.RawConfigParser()
  config_parser.read(['sas.cfg'])
  base_url = config_parser.get('SasTestHarness', 'BaseUrl')
  return base_url

def GetSasUnderTestUrl():
  config_parser = ConfigParser.RawConfigParser()
  config_parser.read(['sas.cfg'])
  sas_uut = config_parser.get('SasConfig', 'BaseUrl')
  return sas_uut


def IsSubString(SubStrList,Str):
  '''''
     SubStrList=['json']
     Str='device_a.json'
     IsSubString(SubStrList,Str)#return True (or False)
     '''
  flag=True
  for substr in SubStrList:
      if not(substr in Str):
          flag=False
  return flag


def GetFileList(FindPath,FlagStr=[]):
  '''''
     get the file name
     FlagStr=['json'] # the file name should contains these string
     FileList=GetFileList(FindPath,FlagStr)
     '''
  FileList=[]
  FileNames=os.listdir(FindPath)
  if (len(FileNames)>0):
     for fn in FileNames:
         if (len(FlagStr)>0):
             if (IsSubString(FlagStr,fn)):
                 FileList.append(fn)
         else:
             FileList.append(fn)

  if (len(FileList)>0):
      FileList.sort()
  return FileList




class SasTestHarness():
  def __init__(self):
    self.logger = logging.getLogger('SAS_TestHarness_Log')
    self.logger.setLevel(logging.INFO)
    self.logger.info('Start sas test harness')
    self._tls_config = TlsConfig().WithClientCertificate(
      self._GetDefaultAdminSSLCertPath(), self._GetDefaultAdminSSLKeyPath())


  def getFullActivityDump(self):
    sas_uut_url = GetSasUnderTestUrl()
    full_activity_dump = FullActivityDumpObject(CERT_FILE, KEY_FILE, sas_uut_url)
    self.cbsd_dump_data = full_activity_dump.cbsd_dump_data
    self.ppa_dump_data = full_activity_dump.ppa_dump_data
    self.esc_dump_data = full_activity_dump.esc_sensor_dump_data
    self.logger.info('Get the Full Activity Dump data')
    self.logger.info('cbsd dump data: ' + self.cbsd_dump_data)
    self.logger.info('ppa dump data: ' + self.ppa_dump_data)
    self.logger.info('esc dump data: ' + self.esc_dump_data)
    return self.cbsd_dump_data, self.ppa_dump_data,self.esc_dump_data

  def sendRegistrationAndGrant(self, registrationRequests, grantRequests):
    self.logger.info('Start send the Registration Requests and Grant Requests')
    self.registration_grant = DomainProxyObject(CERT_FILE, KEY_FILE, registrationRequests, grantRequests)
    self.CbsdObjects = self.registration_grant.CbsdObjects

  def getCbsdObject(self, cbsdId):
    self.logger.info('Get the Cbsd based on the cbsdId: ' + str(cbsdId))
    return self.registration_grant.GetCbsdObject(cbsdId)

  def sendHeartBeatRequest(self):
    self.logger.info('Send Heart Beat Requests of all the Grant Requests')
    self.registration_grant.HeartBeatRequestForAllGrants()

  def getAllCbsdObjectwithAtleastOneGrant(self):
    self.logger.info('Return all the Cbsds with at least one Grant')
    self.registration_grant.GetAllCbsdObjectwithAtleastOneGrant()

  def createCbsd(self, cbsdId, successfulRegRequest, grantId, granRequests):
    self.logger.info('Create cbsd objects')
    self.cbsd = Cbsd(cbsdId,successfulRegRequest,grantId,granRequests)

  def createSingleHeartBeatRequest(self, cbsdId, grantId):
    return self.cbsd.ConstructSingleHeartBeatRequest(cbsdId, grantId)

  def createHeartBeatRequestForAllActiveGrant(self):
    return self.cbsd.ConstructHeartBeatRequestForAllActiveGrant()

  def getPeerSasFAD(self):
    self.logger.info('Get the SAS UUT Full Activity Dump')
    sas_uut_url = GetSasUnderTestUrl()
    self.full_activity_dump = _RequestGet('https://%s' %
                                     (sas_uut_url + '/dump'))
    return self.full_activity_dump

  def getPeerSasPpa(self):
    self.logger.info('Get the all PPA Activity from SAS UUT')
    activity_dump_objects = self.full_activity_dump['files']
    ppa_objects = []
    for object in activity_dump_objects:
      if 'ppa_activity' in object['url']:
        ppa_objects.append(_RequestGet('https://%s' %
                                     (object['url'] + '/dump')))
    return ppa_objects

  def getPeerSasEsc(self):
    self.logger.info('Get the all ESC Activity from SAS UUT')
    activity_dump_objects = self.full_activity_dump['files']
    esc_objects = []
    for object in activity_dump_objects:
      if 'esc_activity' in object['url']:
        esc_objects.append(_RequestGet('https://%s' %
                                       (object['url'] + '/dump')))
    return esc_objects

  def getPeerSasCbsd(self):
    self.logger.info('Get the all CBSD Activity from SAS UUT')
    activity_dump_objects = self.full_activity_dump['files']
    cbsd_objects = []
    for object in activity_dump_objects:
      if 'cbsd_activity' in object['url']:
        cbsd_objects.append(_RequestGet('https://%s' %
                                       (object['url'] + '/dump')))
    return cbsd_objects
  def InjectPeerSas(self,request):
    sas_th_url = GetSasTestHarnessUrl()
    self.logger.info('Inject the SAS Test Harness to SAS UUT')
    _RequestPost('https://%s/admin/injectdata/peer_sas' % sas_th_url,
                 request, self._tls_config)


  def loadMultipleCbsds(self, number):
    key = ['device']
    path = 'testcases/testdata/'
    device_list = GetFileList(path, key)
    devices = []
    if number < len(device_list):
      self.logger.error('Input number larger than existing number of devices')
      return
    for device in device_list:
      device_data = json.load(
        open(os.path.join('testcases', 'testdata', device)))
      devices.append(device_data)
      number -= number
      if number == 0:
        return devices

  def loadMultipleGrants(self, number):
    key = ['grant']
    path = 'testcases/testdata/'
    grant_list = GetFileList(path, key)
    grants = []
    if number < len(grant_list):
      self.logger.error('Input number larger than existing number of grants')
      return
    for grant in grant_list:
      grant_data = json.load(
        open(os.path.join('testcases', 'testdata', grant)))
      grants.append(grant_data)
      number -= number
      if number == 0:
        return grants

  def loadMultiplePpas(self, number):
    key = ['ppa']
    path = 'testcases/testdata/'
    ppa_list = GetFileList(path, key)
    ppas = []
    if number < len(ppa_list):
      self.logger.error('Input number larger than existing number of ppas')
      return
    for ppa in ppa_list:
      ppa_data = json.load(
        open(os.path.join('testcases', 'testdata', ppa)))
      ppas.append(ppa_data)
      number -= number
      if number == 0:
        return ppas

  def loadMultipleEscs(self, number):
    key = ['esc']
    path = 'testcases/testdata/'
    esc_list = GetFileList(path, key)
    escs = []
    if number < len(esc_list):
      self.logger.error('Input number larger than existing number of escs')
      return
    for esc in esc_list:
      esc_data = json.load(
        open(os.path.join('testcases', 'testdata', esc)))
      escs.append(esc_data)
      number -= number
      if number == 0:
        return escs

  def loadMultiplePals(self, number):
    key = ['pal']
    path = 'testcases/testdata/'
    pal_list = GetFileList(path, key)
    pals = []
    if number < len(pal_list):
      self.logger.error('Input number larger than existing number of pals')
      return
    for pal in pal_list:
      pal_data = json.load(
        open(os.path.join('testcases', 'testdata', pal)))
      pals.append(pal_data)
      number -= number
      if number == 0:
        return pals


class SasTestHarnessServer(sas_test_harness_server_interface.HttpServerInterface):
  """Test Harness acting as a Http Server to receive Pull/GET
   Requests from SAS Under Test
   parameters: is the dict variable for different types of dump objects.
   schema of parameters: {
   "full_activity" : dict to store full activity dump objects,
   "cbsd_activity": dict to store cbsd activity dump objects,
   "PPA_activity" : dict to store ppa activity dump objects,
   "esc_activity" : dict to store esc activity dump objects
   }
   schema of full_activity {full activity dump object}
   schema of cbsdActivity {"id": {cbsd activity dump object}}
   schema of ppaActivity {"id": {ppa activity dump object}}
   schema of escActivity {"id": {esc activity dump object}}

  """
  def __init__(self):
    self.parameters = {}

  def setupFullActivity(self, full_activity_dump=None):
    self.parameters['fullActivity'] = full_activity_dump

  def setupCbsdActivity(self, unique_id, Cbsd_activity_dump = None):
    self.parameters['cbsdActivity'][unique_id] = Cbsd_activity_dump

  def setupPpaActivity(self, unique_id, PPA_activity_dump = None):
    self.parameters['ppaActivity'][unique_id] = PPA_activity_dump

  def setupEscActivity(self,unique_id, esc_activity_dump = None):
    self.parameter['escActivity'][unique_id] = esc_activity_dump

  def startServer(self):
    request_handler = SasTestHarnessHandler()
    request_handler.setupParameters(self.parameter)
    self.server = HTTPServer(('localhost', PORT),request_handler)
    self.server.socket = ssl.wrap_socket(
      self.server.socket,
      certfile=CERT_FILE,
      keyfile=KEY_FILE,
      ca_certs=CA_CERT,
      cert_reqs=ssl.CERT_REQUIRED,
      ssl_version=ssl.PROTOCOL_TLSv1_2,
      ciphers=':'.join(CIPHERS),
      server_side=True
      )
    logging.info('Started Test Harness Server')
    # Start Server
    self.server.serve_forever()

  def stopServer(self):
    logging.info('Stopped Test Harness Server')
    self.server.shutdown()

class SasTestHarnessHandler(BaseHTTPRequestHandler):

  def setupParameters(self, parameters):
    self._parameters = parameters

  def do_GET(self):
    """Handles Pull/GET Request and returns Path of the Request to callback Method"""
    if self.path.endswith('/dump'):
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(self._parameters['fullActivity']))
    elif "cbsd_activity" in self.path:
      id = self.path.split('/')[-1]
      if id not in self._parameters['cbsdActivity']:
        self.send_error(404)
        return
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(self._parameters['cbsdActivity'][id]))
    elif "ppa_activity" in self.path:
      id = self.path.split('/')[-1]
      if id not in self._parameters['ppaActivity']:
        self.send_error(404)
        return
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(self._parameters['ppaActivity'][id]))
    elif "esc_activity" in self.path:
      id = self.path.split('/')[-1]
      if id not in self._parameters['escActivity']:
        self.send_error(404)
        return
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(self._parameters['escActivity'][id]))
    else:
      self.send_error(404)




