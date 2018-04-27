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
"""Handles HTTP requests."""

import copy
import json
import logging
import StringIO
import urlparse
import os
import pycurl


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
  """Curl error, as defined in https://curl.haxx.se/libcurl/c/libcurl-errors.html.

  Attributes:
    error_code: integer code representing the pycurl error code. Refer to:
        https://curl.haxx.se/libcurl/c/libcurl-errors.html
  """

  def __init__(self, message, error_code):
    super(CurlError, self).__init__(message)
    self.error_code = error_code


class TlsConfig(object):
  """Holds all TLS/HTTPS parameters."""

  def __init__(self):
    self.ssl_version = pycurl.Curl().SSLVERSION_TLSv1_2
    self.ciphers = [
        'AES128-GCM-SHA256',  # TLS_RSA_WITH_AES_128_GCM_SHA256
        'AES256-GCM-SHA384',  # TLS_RSA_WITH_AES_256_GCM_SHA384
        'ECDHE-ECDSA-AES128-GCM-SHA256',  # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
        'ECDHE-ECDSA-AES256-GCM-SHA384',  # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
        'ECDHE-RSA-AES128-GCM-SHA256',  # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
    ]
    self.ca_cert = os.path.join('certs', 'ca.cert')
    self.client_cert = None
    self.client_key = None

  def WithClientCertificate(self, client_cert, client_key):
    """Returns a copy of the current config with the given certificate and key.

    Required for security tests.
    """
    ret = copy.copy(self)
    ret.client_key = client_key
    ret.client_cert = client_cert
    return ret


def RequestPost(url, request, config):
  return _Request(url, request, config, True)


def RequestGet(url, config):
  return _Request(url, None, config, False)


def _Request(url, request, config, is_post_method):
  """Sends HTTPS request.

  Args:
    url: Destination of the HTTPS request.
    request: Content of the request. (Can be None)
    config: a |TlsConfig| object defining the TLS/HTTPS configuration.
    is_post_method (bool): If True, use POST, else GET.
  Returns:
    A dictionary represents the JSON response received from server.
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
  conn.setopt(
      conn.VERBOSE,
      3  # Improve readability.
      if logging.getLogger().isEnabledFor(logging.DEBUG) else False)
  conn.setopt(conn.SSLVERSION, config.ssl_version)
  conn.setopt(conn.SSLCERTTYPE, 'PEM')
  conn.setopt(conn.SSLCERT, config.client_cert)
  conn.setopt(conn.SSLKEY, config.client_key)
  conn.setopt(conn.CAINFO, config.ca_cert)
  conn.setopt(conn.HTTPHEADER, header)
  conn.setopt(conn.SSL_CIPHER_LIST, ':'.join(config.ciphers))
  request = json.dumps(request) if request else ''
  if is_post_method:
    conn.setopt(conn.POST, True)
    conn.setopt(conn.POSTFIELDS, request)
    logging.info('POST Request to URL %s :\n%s', url, request)
  else:
    logging.info('GET Request to URL %s', url)
  try:
    conn.perform()
  except pycurl.error as e:
    # e contains a tuple (libcurl_error_code, string_description).
    # See https://curl.haxx.se/libcurl/c/libcurl-errors.html
    raise CurlError(e.args[1], e.args[0])
  http_code = conn.getinfo(pycurl.HTTP_CODE)
  conn.close()
  body = response.getvalue()
  logging.info('Response:\n' + body)

  if not (200 <= http_code <= 299):
    raise HTTPError(http_code)
  if body:
    return json.loads(body.decode('utf-8'))
