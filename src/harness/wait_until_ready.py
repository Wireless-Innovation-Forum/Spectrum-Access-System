"""Helper tool to try resetting the SAS until the reset is completed successfully.
Once the script exits successfully, the SAS is once again ready for testing.

Usage: python wait_until_ready.py <Put SAS URL here> admin.cert admin.key ca.cert

Note: the example usage above assumes that the script is in the same directory as the
certs, i.e. it is in src/harness/certs/. You can also copy the necessary certs to any
folder and run the script from there (i.e. it need not be run from "within" the test
harness).
"""

from __future__ import print_function

import argparse
import StringIO
import time
import urlparse

import pycurl


# The maximum timeto retry reset, in hours.
MAX_TIMEOUT_HOURS = 4


# Basicaly adapted from src/harness/request_handler.py
class HTTPError(Exception):
  """HTTP error, ie. any HTTP code not in range [200, 299].

  Attributes:
    error_code: integer code representing the HTTP error code. Refer to:
        https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
  """

  def __init__(self, error_code):
    super(HTTPError, self).__init__('HTTP code %d' % error_code)
    self.error_code = error_code


class CurlError(Exception):
  """Curl error, from https://curl.haxx.se/libcurl/c/libcurl-errors.html.

  Attributes:
    error_code: integer code representing the pycurl error code. Refer to:
        https://curl.haxx.se/libcurl/c/libcurl-errors.html
  """

  def __init__(self, message, error_code):
    super(CurlError, self).__init__(message)
    self.error_code = error_code


def PostRequest(url, client_cert, client_key, ca_cert):
  """Sends HTTPS POST empty request.

  Args:
    url: Destination of the HTTPS request.
    client_cert: file path of the client certificate
    client_key: file path of the client private key
    ca_cert: file path of the trusted CA certificate
  Raises:
    CurlError: with args[0] is an integer code representing the libcurl
      SSL code response (value < 100). Refer to:
      https://curl.haxx.se/libcurl/c/libcurl-errors.html
    HTTPError: for any HTTP code not in the range [200, 299]. Refer to:
      https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)
  """
  response = StringIO.StringIO()
  conn = pycurl.Curl()
  conn.setopt(conn.URL, url)
  conn.setopt(conn.WRITEFUNCTION, response.write)
  header = [
      'Host: %s' % urlparse.urlparse(url).hostname,
      'content-type: application/json'
  ]
  #conn.setopt(conn.VERBOSE, 3)  # Improve readability.
  conn.setopt(conn.VERBOSE, False)
  conn.setopt(conn.SSLVERSION, pycurl.Curl().SSLVERSION_TLSv1_2)
  conn.setopt(conn.SSLCERTTYPE, 'PEM')
  conn.setopt(conn.SSLCERT, client_cert)
  conn.setopt(conn.SSLKEY, client_key)
  conn.setopt(conn.CAINFO, ca_cert)
  conn.setopt(conn.HTTPHEADER, header)
  conn.setopt(conn.SSL_CIPHER_LIST, 'AES128-GCM-SHA256')
  conn.setopt(conn.TCP_KEEPALIVE, 1)
  conn.setopt(conn.POST, True)
  conn.setopt(conn.POSTFIELDS, '')
  try:
    conn.perform()
  except pycurl.error as e:
    # e contains a tuple (libcurl_error_code, string_description).
    # See https://curl.haxx.se/libcurl/c/libcurl-errors.html
    raise CurlError(e.args[1], e.args[0])
  http_code = conn.getinfo(pycurl.HTTP_CODE)
  conn.close()

  if not 200 <= http_code <= 299:
    print('Response:\n%s', response.getvalue())
    raise HTTPError(http_code)


def ResetWithRetry(base_url, client_cert, client_key, ca_cert):
  """Resets a SAS, doing retry in case of timeout error.

  Args:
    base_url: base URL of a SAS, as defined in the winnforum config file
    client_cert: file path of the client certificate
    client_key: file path of the client private key
    ca_cert: file path of the trusted CA certificates
  """
  now = time.time()
  max_limit = now + MAX_TIMEOUT_HOURS * 3600
  while now < max_limit:
    try:
      PostRequest('https://%s/admin/reset' % base_url, client_cert, client_key,
                  ca_cert)
      print('Reset was successful! The SAS is now ready for more testing.')
      break
    except HTTPError as e:
      # Intercept only RequestTimeout and GatewayTimeout.
      if e.error_code not in (408, 504):
        raise
      # Wait the same time that the request delay...
      print('Reset produced timeout... Waiting for %fs', time.time() - now)
      time.sleep(time.time() - now)
      now = time.time()
      if now >= max_limit:
        raise


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Reset a SAS with retry on timeout')
  parser.add_argument('base_url',
                      help='Base URL of a SAS, as defined in the winnforum '
                      'config file, e.g. "sas-url.com/instance1"')
  parser.add_argument('client_cert', help='File path of the client certificate')
  parser.add_argument('client_key', help='File path of the client private key')
  parser.add_argument('ca_cert', help='File path of the trusted CA certificate')

  args = parser.parse_args()
  ResetWithRetry(args.base_url, args.client_cert, args.client_key, args.ca_cert)
