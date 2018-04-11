#  Copyright 2018 SAS Project Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""A simple Certificate Revocation List (CRL) server implementation."""

import inspect
import logging
import os
import socket
import sys
import subprocess
import threading
from urlparse import urlparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

DEFAULT_CRL_URL = 'http://localhost:9007/ca.crl'
DEFAULT_CRL_SERVER_PORT = 80
MENU_ACTIONS = {}
MENU_ID_MAIN_MENU = '-1'
MENU_ID_QUIT = '0'
MENU_ID_REVOKE_CERT = '1'
MENU_ID_CRL_UPDATE_REGENERATE = '2'
BANNER_TITLE = r'''   _____ _____  _         _____
  / ____|  __ \| |       / ____|
 | |    | |__) | |      | (___   ___ _ ____   _____ _ __
 | |    |  _  /| |       \___ \ / _ \ '__\ \ / / _ \ '__|
 | |____| | \ \| |____   ____) |  __/ |   \ V /  __/ |
  \_____|_|  \_\______| |_____/ \___|_|    \_/ \___|_|
 '''
MENU_OPTIONS = '''
Please select the options:
[1] Revoke Certificate
[2] Update CRL URL and Re-generate certificates
[0] Quit'''
CLI_PROMPT_TEXT = '''CRL Server> '''


class SimpleCrlServer(threading.Thread):
  """Implements a simple CRL server by creating a HTTP server.

  A simple HTTP server that responds with the ca.crl file present in the 'harness/certs/crl/' directory serving CRL files.
  The CRL server runs as a separate thread.
  """

  def __init__(self, crl_url, crl_file_path):
    """Constructor for simple CRL Server.

    Args:
      crl_url: The URL that is mentioned in the CDP extension of the certificates.
        The CRL server runs on this URL and responds only to this URL with the CRL file.
      crl_file_path: Absolute path to the CRL file that will be served by this CRL server.
    """

    super(SimpleCrlServer, self).__init__()
    url_components = urlparse(crl_url)
    self.host_name = url_components.hostname
    self.port = url_components.port if url_components.port is not None else \
      DEFAULT_CRL_SERVER_PORT
    self.crl_url_path = url_components.path
    self.crl_file_path = crl_file_path
    self.setDaemon(True)

    # Setting the parameters for handler class.
    self.server = CrlHttpServer(self.crl_url_path, self.crl_file_path,
                                (self.host_name, self.port),
                                CrlServerHttpHandler)

  def run(self):
    """Starts the HTTPServer as background thread.

    The run() method is an overridden method from thread class and it gets invoked
    when the thread is started using thread.start().
    """

    logging.info("Started CRL Server at %s", self.host_name + ":" + str(self.port))
    self.server.serve_forever()

  def stopServer(self):
    """This method is used to stop HTTPServer Socket"""

    self.server.shutdown()
    logging.info('Stopped CRL Server at %s', self.host_name + ":" + str(self.port))

class CrlHttpServer(HTTPServer):
  """The class CrlHttpServer overrides built-in HTTPServer.

  It takes the parameter base_path used to serve the files.
  This is needed to have CRL Server to serve files from different directories.
  """

  def __init__(self, crl_url_path, crl_file_path, server_address, RequestHandlerClass):
    self.crl_url_path = crl_url_path
    self.crl_file_path = crl_file_path
    HTTPServer.__init__(self, server_address, RequestHandlerClass)

class CrlServerHttpHandler(BaseHTTPRequestHandler):
  """This class implements the HTTP handlers for the CRL Server.

  CrlServerHttpHandler class inherits with BaseHTTPRequestHandler
  to serve HTTP Response.
  """

  def do_GET(self):
    """Handles Pull/GET Request and returns path of the request to callback method."""

    parsed_path = urlparse(self.path)
    self.log_message('Received GET Request:{}'.format(parsed_path.path))

    # Handles the GET Requests.
    # If the GET request path does not match the CRL URL path then respond with 404 response.
    if parsed_path.path != self.server.crl_url_path:
      self.log_message('Requested url :{0} does not match with CRL Server URL '
                       'path:{1}'.format(parsed_path.path, self.server.crl_url_path))
      self.send_response(404)
      return

    # Load the ca.crl and write content in HTTP response stream with 200 OK response.
    # If any exception occurs while reading CRL chain and handle error and respond
    # with 404 'Not Found' response.
    try:
      with open(os.path.join(self.server.crl_file_path)) as file_handle:
        file_data = file_handle.read()
    except IOError:
      self.log_message('There is an error reading file:{}'.format(
          self.server.crl_file_path))
      self.send_response(404)
      return
    else:
      self.send_response(200)
      self.send_header("Content-type", "application/pkix-crl")
      self.end_headers()
      self.wfile.write(file_data)
      return

def getCertsDirectoryAbsolutePath():
  """This function will return absolute path of 'certs' directory."""

  harness_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
  path = os.path.join(harness_dir, 'certs')
  return path

def getCertificateNameToBlacklist():
  """Allows the user to select the certificate to blacklist from a displayed list."""

  # Gets the all certificate files that are ends with .cert present in the
  # default certs directory.
  cert_files = [cert_file_name for cert_file_name in os.listdir(
      getCertsDirectoryAbsolutePath()) if cert_file_name.endswith('.cert')]

  # Creates the mapping menu ID for each certificate file to displayed list.
  cert_files_with_options = dict(zip(range(len(cert_files)), sorted(cert_files)))
  print "Select the certificate to blacklist:"
  print "\n".join("[%s] %s" % (cert_file_option_id, cert_file_name)
                  for (cert_file_option_id, cert_file_name) in
                  sorted(cert_files_with_options.iteritems()))
  option_id = int(raw_input(CLI_PROMPT_TEXT))
  if option_id not in cert_files_with_options:
    raise Exception('RunTimeError:Invalid input:{}. Please select a valid '
                    'certificate'.format(option_id))
  return cert_files_with_options[option_id]


def revokeCertificate():
  """Revokes a leaf certificate and updates the CRL chain file."""

  # Retrives the all certificates from certs directory.
  cert_name = getCertificateNameToBlacklist()
  logging.info('Certificate selected to blacklist is:%s', cert_name)
  revoke_cert_command = "cd {0} && bash ./revoke_and_generate_crl.sh " \
                        "-r {1}".format(getCertsDirectoryAbsolutePath(),
                                         cert_name)
  command_exit_status = subprocess.call(revoke_cert_command, shell=True)
  if command_exit_status:
    raise Exception("RunTimeError:Certificate Revocation is failed:"
                    "exit_code:{}".format(command_exit_status))
  logging.info('%s is blacklisted successfully', cert_name)


def updateCrlUrlAndRegenerateCertificates():
  """Updates the CDP  field and re-generates certificates.

  Updates URI.0 field in the in openssl.cnf file with the CRL URL of this simple CRL
  server. Invokes the generate_fake_certs.sh script to regenerate all certificates.
  """

  # Update CRL URL in openssl.cnf.
  crl_url = 'URI.0 = {}'.format(DEFAULT_CRL_URL)
  update_crl_section_command = (r"sed -i -e 's~^URI.0\s=\s.*$~%s~1' ../../cert/openssl.cnf"
                                % crl_url)
  command_exit_status = subprocess.call(update_crl_section_command, shell=True)
  if command_exit_status:
    raise Exception("RunTimeError:Could not update CRL URL in openssl.cnf:"
                    "exit_code:{}".format(command_exit_status))
  logging.info('CRL URL has been updated correctly in openssl.cnf')

  # Re-generate certificates.
  script_name = 'bash ./generate_fake_certs.sh'
  command = 'cd {0} && {1}'.format(getCertsDirectoryAbsolutePath(), script_name)
  command_exit_status = subprocess.call(command, shell=True)
  if command_exit_status:
    raise Exception("RunTimeError:Regeneration of certificates failed:"
                    "exit_code:{}".format(command_exit_status))
  logging.info("The certs are regenerated successfully")

  # Generate CRL Chain.
  generateCrlChain()


def generateCrlChain():
  """ Generate CRL Chain for the intermediate CAs.

  It creates a CRL file for the intermediate CAs (CBSD CA, DP CA and SAS CA) and the root CA.
  All the CRL files are concatenated to create CRL chain file named ca.crl and
  placed in the 'harness/certs/crl/' directory.
  """

  create_crl_chain_command = "cd {0} && bash ./revoke_and_generate_crl.sh -u".format(
      getCertsDirectoryAbsolutePath())
  command_exit_status = subprocess.call(create_crl_chain_command, shell=True)
  if command_exit_status:
    raise Exception("RunTimeError:Creation CRL chain is failed:"
                    "exit_code:{}".format(command_exit_status))
  if not os.path.exists(os.path.join(getCertsDirectoryAbsolutePath(),
                                     'crl/ca.crl')):
    raise Exception("RunTimeError:crl/ca.crl is not found:"
                    "exit_code:{}".format(command_exit_status))
  logging.info('crl/ca.crl CRL chain is created successfully')


def crlServerStart():
  """Start CRL server."""

  # Create CRL chain containing CRLs of sub CAs and root CA.
  generateCrlChain()

  try:
    crl_server = SimpleCrlServer(DEFAULT_CRL_URL, os.path.join(getCertsDirectoryAbsolutePath(),
                                                               'crl/ca.crl'))
    crl_server.start()
    logging.info("CRL Server has been started")
    logging.info('CRL Server URL:%s' % DEFAULT_CRL_URL)
  except socket.error as err:
    raise Exception("RunTimeError:There is an error starting CRL Server:"
                    "exit_reason:{}".format(err.strerror))

  return crl_server

def crlServerStop(crl_server):
  """Stop CRL Server.

  Args:
    crl_server: A CRL Server object instance.
  """

  crl_server.stopServer()

def readInput():
  """Display the CRL server menu and executes the selected option."""

  print BANNER_TITLE + MENU_OPTIONS
  choice = raw_input(CLI_PROMPT_TEXT)
  executeSelectedMenu(choice)
  return

def executeSelectedMenu(choice):
  """Performs the action based on the selected menu item.

  Args:
    choice: The selected index value from the main menu of CRL server.
  """

  if choice == '':
    MENU_ACTIONS[MENU_ID_MAIN_MENU]()
  else:
    try:
      MENU_ACTIONS[choice]()
    except KeyError:
      print "Invalid selection, please try again"
    except Exception as err:
      logging.error(err.message)
    MENU_ACTIONS[MENU_ID_MAIN_MENU]()
  return

# Mapping menu items to handler functions.
MENU_ACTIONS = {
    MENU_ID_MAIN_MENU: readInput,
    MENU_ID_REVOKE_CERT: revokeCertificate,
    MENU_ID_CRL_UPDATE_REGENERATE: updateCrlUrlAndRegenerateCertificates,
    MENU_ID_QUIT: exit
}

# Set the logger for CRL Server.
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

if __name__ == '__main__':
  # Start Simple CRL Server and waits for user input.
  try:
    crl_server_instance = crlServerStart()
    readInput()
    crlServerStop(crl_server_instance)
  except Exception as err:
    logging.error(err.message)
