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

"""
    A fake implementation of Certificate Revocation list Server.
"""
import logging
import threading
import urlparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


class FakeCrlServerTestHarness(threading.Thread):
    """Implements a fake CRL server by creating a HTTP server and serving CRL files.
        The fake CRL server runs as a separate thread"""
    def __init__(self,host_name, port, crl_url, crl_file_name):
        """Constructor for fake CRL test harness
            Requests from SAS Under Test
        "host_name": entity hosting the fake crl server
        "port" : port number at which fake crl server will run
        "crl_url" :  name of the crl url to be validated
        "crl_file_name" : Name of the crl file
        """
        super(FakeCrlServerTestHarness, self).__init__()
        self.parameters = {
            "hostName":host_name,
            "port": int(port),
            "crlUrl": crl_url,
            "crlFileName": crl_file_name
        }
        self.daemon = True

    def run(self):
        """Starts the HTTP server at host name and port"""
        # Setting the parameters for handler class
        logging.info("Started fake CRL Server at %s",
                     self.parameters['hostName']+":" + str(self.parameters['port']))
        FakeCrlServerTestHarnessHandler._parameters = self.parameters
        self.server = HTTPServer((self.parameters['hostName'], self.parameters['port']),
                                 FakeCrlServerTestHarnessHandler)
        self.server.serve_forever()

    def stopServer(self):
        """shutdown of the HTTP server"""
        self.server.shutdown()
        logging.info('fake CRL Server shutdown %s',
                     self.parameters['hostName']+":" + str(self.parameters['port']))


class FakeCrlServerTestHarnessHandler(BaseHTTPRequestHandler, FakeCrlServerTestHarness):
    _parameters = None

    def do_GET(self):
        """Handles GET requests"""
        parsed_path = urlparse.urlparse(self.path)
        logging.info('Received GET Request %s',parsed_path.path)
        if( parsed_path.path == ("/"+FakeCrlServerTestHarnessHandler._parameters['crlUrl'])):
            # Handles the GET Requests
            file_object = open(FakeCrlServerTestHarnessHandler._parameters['crlFileName'])
            self.wfile.write(file_object.read())
            self.send_header("Content-type", "application/pkix-crl")
            self.send_response(200)
            file_object.close()
        else:
            self.wfile.write("\n FILE NOT FOUND \n")
            logging.info('Requested file not found  %s', parsed_path.path)
            self.send_response(404)
