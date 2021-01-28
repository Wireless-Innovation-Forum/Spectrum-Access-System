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
"""Helper functions for test harness."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import defaultdict
from datetime import datetime
from functools import wraps
import inspect
import json
import logging
import os
import random
import sys
import time
import uuid

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import rsa
from jsonschema import validate, Draft4Validator, RefResolver
import jwt
import portpicker
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from shapely.geometry import shape, Point, LineString
import six
from six.moves import configparser
from six.moves import range

from util2 import makePalRecordsConsistent, makePpaAndPalRecordsConsistent, assertContainsRequiredFields
from reference_models.geo import utils

def json_load(fname):
  with open(fname) as fd:
    return json.load(fd)

def _log_testcase_header(name, doc):
  if not len(logging.getLogger().handlers):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
      logging.Formatter(
        '[%(levelname)s] %(asctime)s %(filename)s:%(lineno)d %(message)s'))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
  logging.info('Running WinnForum test case %s:', name)
  logging.info(doc)


def winnforum_testcase(testcase):
  """Decorator for common features (e.g. logging) for WinnForum test cases."""
  def decorated_testcase(*args, **kwargs):
    if not testcase:
      raise ValueError('Avoid using @winnforum_testcase with '
                       '@configurable_testcase')
    _log_testcase_header(testcase.__name__, testcase.__doc__)
    testcase(*args, **kwargs)

  return decorated_testcase


def configurable_testcase(default_config_function):
  """Decorator to make a test case configurable."""

  def internal_configurable_testcase(testcase):

    _log_testcase_header(testcase.__name__, testcase.__doc__)

    def wrapper_function(func, name, config, generate_default_func):
      @wraps(func)
      def _func(*a):
        if generate_default_func:
          generate_default_func(*a)
          _releaseAllPorts()
        _log_testcase_header(name, func.__doc__)
        return func(*a, config_filename=config)
      _func.__name__ = name
      return _func

    def generate_default(func, default_filename):
      @wraps(func)
      def _func(*a):
        return func(*a, filename=default_filename)
      return _func

    # Create config directory for this function if it doesn't already exist.
    harness_dir = os.path.dirname(
              os.path.abspath(inspect.getfile(inspect.currentframe())))
    config_dir = os.path.join(harness_dir, 'testcases', 'configs',
                              testcase.__name__)
    config_names = os.listdir(config_dir) if os.path.exists(config_dir) else []

    # No existing configs => generate default config.
    generate_default_func = None
    if not config_names:
      default_config_filename = os.path.join(config_dir, 'default.config')
      logging.info("%s: Creating default config at '%s'", testcase.__name__,
                   default_config_filename)
      generate_default_func = generate_default(default_config_function,
                                               default_config_filename)
      config_names.append('default.config')

    # Run once for each config.
    stack = inspect.stack()
    frame = stack[1]  # Picks the 'testcase' frame.
    frame_locals = frame[0].f_locals
    for i, config_name in enumerate(config_names):
      base_config_name = os.path.splitext(config_name)[0]
      name = '%s_%d_%s' % (testcase.__name__, i, base_config_name)
      config_filename = os.path.join(config_dir, config_name)
      frame_locals[name] = wrapper_function(testcase, name, config_filename,
                                            generate_default_func)

  return internal_configurable_testcase


def loadConfig(config_filename):
  """Loads a configuration file."""
  with open(config_filename, 'rb') as f:
    return json.loads(f.read())


def writeConfig(config_filename, config):
  """Writes a configuration file."""
  dir_name = os.path.dirname(config_filename)
  if not os.path.exists(dir_name):
    os.makedirs(dir_name)

  with open(config_filename, 'w') as f:
    f.write(
        json.dumps(config, indent=2, sort_keys=False, separators=(',', ': ')))


def getRandomLatLongInPolygon(ppa):
  """Generates a random point inside the PPA Polygon.

  Note: since the generated point is NOT uniformly distributed within the PPA,
  do not rely on this function if you want a purely uniform distribution.

  Args:
    ppa: (dictionary) A dictionary containing PPA Record.
  Returns:
    A tuple (lat, lon) with the point coordinates.
  """

  try:
    ppa_polygon = shape(ppa['zone']['features'][0]['geometry'])
    min_lng, min_lat, max_lng, max_lat = ppa_polygon.bounds
    lng = random.uniform(min_lng, max_lng)
    lng_line = LineString([(lng, min_lat), (lng, max_lat)])
    lng_line_intercept_min, lng_line_intercept_max = lng_line.intersection(ppa_polygon).xy[1].tolist()
    lat = random.uniform(lng_line_intercept_min, lng_line_intercept_max)
    if Point([lng, lat]).within(ppa_polygon):
      return lat, lng
    else:
      return getRandomLatLongInPolygon(ppa)
  except NotImplementedError:
    # Cannot get the intercept call it again
    return getRandomLatLongInPolygon(ppa)


def generateCpiRsaKeys():
  """Generate a private/public RSA 2048 key pair.

  Returns:
    A tuple (private_key, public key) as PEM string encoded.
  """
  rsa_key = rsa.generate_private_key(
      public_exponent=65537, key_size=2048, backend=default_backend())
  rsa_private_key = rsa_key.private_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PrivateFormat.TraditionalOpenSSL,
      encryption_algorithm=serialization.NoEncryption())
  rsa_public_key = rsa_key.public_key().public_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PublicFormat.SubjectPublicKeyInfo)
  return six.ensure_text(rsa_private_key), six.ensure_text(rsa_public_key)


def generateCpiEcKeys():
  """Generate a private/public EC SECP256R1 key pair.

    Returns:
      A tuple (private_key, public key) as PEM string encoded.
    """
  ec_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
  ec_private_key = ec_key.private_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PrivateFormat.TraditionalOpenSSL,
      encryption_algorithm=serialization.NoEncryption())
  ec_public_key = ec_key.public_key().public_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PublicFormat.SubjectPublicKeyInfo)
  return six.ensure_text(ec_private_key), six.ensure_text(ec_public_key)


def convertRequestToRequestWithCpiSignature(private_key, cpi_id,
                                            cpi_name, request,
                                            jwt_algorithm='RS256'):
  """Converts a regular registration request to contain cpiSignatureData
       using the given JWT signature algorithm.

    Args:
      private_key: (string) valid PEM encoded string.
      cpi_id: (string) valid cpiId.
      cpi_name: (string) valid cpiName.
      request: individual CBSD registration request (which is a dictionary).
      jwt_algorithm: (string) algorithm to sign the JWT, defaults to 'RS256'.
    """
  cpi_signed_data = {}
  cpi_signed_data['fccId'] = request['fccId']
  cpi_signed_data['cbsdSerialNumber'] = request['cbsdSerialNumber']
  cpi_signed_data['installationParam'] = request['installationParam']
  del request['installationParam']
  cpi_signed_data['professionalInstallerData'] = {}
  if cpi_id:
    cpi_signed_data['professionalInstallerData']['cpiId'] = cpi_id
  cpi_signed_data['professionalInstallerData']['cpiName'] = cpi_name
  cpi_signed_data['professionalInstallerData'][
      'installCertificationTime'] = datetime.utcnow().strftime(
          '%Y-%m-%dT%H:%M:%SZ')
  compact_jwt_message = jwt.encode(
      cpi_signed_data, private_key, jwt_algorithm)
  jwt_message = six.ensure_text(compact_jwt_message).split('.')
  request['cpiSignatureData'] = {}
  request['cpiSignatureData']['protectedHeader'] = jwt_message[0]
  request['cpiSignatureData']['encodedCpiSignedData'] = jwt_message[1]
  request['cpiSignatureData']['digitalSignature'] = jwt_message[2]


def addIdsToRequests(ids, requests, id_field_name):
  """Adds CBSD IDs or Grant IDs to any given request.

  This function uses the following logic:
   - If the ID field is missing in request[i], it is filled with ids[i].
     - Note: len(ids) == len(requests) is required in this case.
   - If the ID field in request[i] is equal to 'REMOVE', the field is deleted.
   - If the ID field in request[i] is an integer k, it is replaced with ids[k].

  Args:
    ids: (list) a list of valid CBSD IDs or Grant IDs.
    requests: (list) list of requests, can contain empty dictionaries.
    id_field_name: (string) 'cbsdId' or 'grantId'.
  """
  for index, req in enumerate(requests):
    if id_field_name not in req:
      if len(ids) != len(requests):
        raise ValueError('Bad number of requests')
      req[id_field_name] = ids[index]
    elif req[id_field_name] == 'REMOVE':
      del req[id_field_name]
    elif isinstance(req[id_field_name], int):
      req[id_field_name] = ids[req[id_field_name]]
    # Else use the value that was provided in the config directly.


def addCbsdIdsToRequests(cbsd_ids, requests):
  """Adds CBSD IDs to a given request. See addIdsToRequests() for more info.

  Args:
    cbsd_ids: (list) list of CBSD IDs to be inserted into the request.
    requests: (list) list of requests, containing dictionaries.
  """
  addIdsToRequests(cbsd_ids, requests, 'cbsdId')


def addGrantIdsToRequests(grant_ids, requests):
  """Adds Grant IDs to a given request. See addIdsToRequests() for more info.

  Args:
    grant_ids: (list) list of Grant IDs to be inserted into the request.
    requests: (list) list of requests, containing dictionaries.
  """
  addIdsToRequests(grant_ids, requests, 'grantId')

def getCertificateFingerprint(certificate):
  """ Get SHA1 hash of the input certificate.
  Args:
    certificate: The full path to the file containing the certificate
  Returns:
    sha1 fingerprint of the input certificate
  """
  certificate_string = open(certificate,"rb").read()
  cert = load_certificate(FILETYPE_PEM, certificate_string)
  sha1_fingerprint = cert.digest("sha1")
  return six.ensure_text(sha1_fingerprint)

def filterChannelsByFrequencyRange(channels, freq_range):
  """Returns channels which partially or fully overlap with 'freq_range'.

  Args:
    channels: list of available channels.
    freq_range: dict of frequency range.
  """

  return [
      channel for channel in channels
      if
      channel['frequencyRange']['lowFrequency'] < freq_range['highFrequency']
      and
      channel['frequencyRange']['highFrequency'] > freq_range['lowFrequency']
  ]

def _orderAttributes(obj):
  if isinstance(obj, dict):
    return sorted((k, _orderAttributes(v)) for k, v in obj.items())
  if isinstance(obj, list):
    return sorted(_orderAttributes(x) for x in obj)
  else:
    return obj

def compareDictWithUnorderedLists(first_dict, second_dict):
  """ Deep comparison of two dictionaries

  Args:
    first_dict: first dictionary to be compared.
    second_dict: second dictionary to be compared.
 Returns: boolean set to true if the dictionaries are equal and false otherwise.
  """
  return _orderAttributes(first_dict) == _orderAttributes(second_dict)

def areTwoPpasEqual(first_ppa, second_ppa, delta=10):
  """ Deep comparison of two PPAs considering

  Args:
    first_ppa: a dictionary contains  the firt PPA data.
    second_ppa: a dictionary contains the second PPA data.
    delta: an accepted margin for comparing the polygons of PPAs

 Returns: boolean set to true if the PPAs are equal and false otherwise.
 Note: the PPA should contain a key 'zone' holding a GeoJSON feature collection with first feature
     defining the PPA zone as a polygon (or multipolygon) geometry
  """
  geometry_of_first_ppa = first_ppa['zone']['features'][0]['geometry']
  geometry_of_second_ppa = second_ppa['zone']['features'][0]['geometry']

  if not utils.PolygonsAlmostEqual(geometry_of_first_ppa, geometry_of_second_ppa, delta):
    return False
  if geometry_of_first_ppa['type'] != geometry_of_second_ppa['type']:
    return False
  # check other Ppa parameters
  del first_ppa['zone']['features'][0]['geometry']
  del second_ppa['zone']['features'][0]['geometry']
  result = compareDictWithUnorderedLists(first_ppa, second_ppa)
  first_ppa['zone']['features'][0]['geometry'] = geometry_of_first_ppa
  second_ppa['zone']['features'][0]['geometry'] = geometry_of_second_ppa
  return result

def buildDpaActivationMessage(dpa_config):
  """Constructs a dpa activation message."""
  return {
      'dpaId': dpa_config['dpaId'],
      'frequencyRange': dpa_config['frequencyRange']
  }

class TestComponentError(Exception):
  """Indicates a test component failed due to no fault of the SAS UUT.

  Some test components are theoretically capable of failing through no fault of
  the SAS UUT. If a failure happens that is clearly not the fault of the SAS UUT
  this exception may be raised to indicate the test result is invalid and the
  test should be rerun. Please indicate the component that failed in the
  message to help with analysis of repeated failures.
  """
  pass

def getFUGPoints(ppa):
  """This function returns FUG points list
    Args:
      ppa: (dictionary) A dictionary containing PPA/GWPZ Record.
    Returns:
      An array of tuple (lat, lng).
    """
  fug_points = []
  ppa_polygon = shape(ppa[0]['zone']['features'][0]['geometry'])
  min_lng, min_lat, max_lng, max_lat = ppa_polygon.bounds
  upper_boundary_lng = np.ceil(max_lng)
  lower_boundary_lng = np.floor(min_lng)
  upper_boundary_lat = np.ceil(max_lat)
  lower_boundary_lat = np.floor(min_lat)
  while(upper_boundary_lat >= lower_boundary_lat):
    while(upper_boundary_lng >= lower_boundary_lng):
      pointLat = round(upper_boundary_lat, 6)
      pointLng = round(upper_boundary_lng, 6)
      if Point([pointLng, pointLat]).within(ppa_polygon):
        fug_points.append((pointLat, pointLng))
      upper_boundary_lng = upper_boundary_lng - 2.0 / 3600
    upper_boundary_lat = upper_boundary_lat - 2.0 / 3600
    upper_boundary_lng = max_lng + 2.0 / 3600
  return fug_points


def getChannels(lowFrequency, highFrequency):
  """This function returns protected channels list"""
  protection_channels = []
  startFrequency = 3550
  channel = 0
  while channel < 30:
    if ((startFrequency+channel*5 < lowFrequency/1000000 and startFrequency + (channel+1)*5 > lowFrequency/1000000)
            or (startFrequency+channel*5 >= lowFrequency/1000000 and startFrequency + (channel+1)*5 <= highFrequency/1000000)
            or (startFrequency+channel*5 < highFrequency/1000000 and startFrequency + (channel+1)*5 > highFrequency/1000000)):
      ch_low_freq = (startFrequency * 1000000) + (channel * 5000000)
      ch_high_freq = ch_low_freq + 5000000
      protection_channels.append((ch_low_freq, ch_high_freq))
    channel = channel + 1
  return protection_channels

def ensureFileDirectoryExists(file_path):
  dir_name = os.path.dirname(file_path)
  if not os.path.exists(dir_name):
    os.makedirs(dir_name)

def getCertFilename(cert_name):
  """Returns the file path corresponding to the given |cert_name|.
  """
  return os.path.join('certs', cert_name)


class _TestConfig(object):
  """Represents the configuration of a Test Harness."""

  def __init__(self):
    self.hostname = 'localhost'
    self.min_port = 9005
    self.max_port = 9010

  @classmethod
  def FromFile(cls, file='test.cfg'):
    parser = configparser.RawConfigParser()
    parser.read([file])
    test_config = _TestConfig()
    test_config.hostname = parser.get('TestConfig', 'hostname')
    test_config.min_port = int(parser.get('TestConfig', 'minPort'))
    test_config.max_port = int(parser.get('TestConfig', 'maxPort'))
    return test_config


_test_config = None
def _GetSharedTestConfig():
  global _test_config
  if _test_config is None:
    _test_config = _TestConfig.FromFile()
  return _test_config

def getFqdnLocalhost():
  """Returns the fully qualified name of the host running the testcase.
  To be used when starting peer SAS webserver or other database webserver.
  """
  return _GetSharedTestConfig().hostname

_ports = set()
def getUnusedPort():
  """Returns an unused TCP port on the local host inside the defined port range.
  To be used when starting peer SAS webserver or other database webserver.
  """
  config = _GetSharedTestConfig()
  if config.min_port < 0:
    return portpicker.pick_unused_port()
  global _ports
  # Find the first available port in the defined range.
  for p in range(config.min_port, config.max_port):
    if p not in _ports and portpicker.is_port_free(p):
      _ports.add(p)
      return p
  raise AssertionError('No available new ports')

def releasePort(port):
  """Release a used port after a webserver goes down."""
  if _GetSharedTestConfig().min_port < 0:
    portpicker.return_port(port)
  global _ports
  if port in _ports:
    _ports.remove(port)

def _releaseAllPorts():
  """Release all used ports."""
  _ports.clear()
