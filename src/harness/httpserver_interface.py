import abc
class HttpServerInterface(object):
  @abc.abstractmethod
  def setupServer(self, parameters=None):
    """Http Server interface to get the response based on the Pull/GET or Push/POST Request
    Args:
      parameters: A dictionary with the following key-value pairs:
        response_body:(dictionary) the response object which will be send to SAS Under Test
        when the request is successful.
        expected_path: (string) the path after the Base Url which SAS Under Test will call to
        make Push/Pull Request.
    Returns:
      Reference to a method which when called will wait for the request from SAS Under Test
      and will return the response of the request made by SAS Under Test based on the following
      criteria:
        1. If the request type is Pull/GET and expected path is correct then it will return
        the path and empty body of the request made by SAS Under Test or else will give
        HTTP 404 error.
        2. If the request type is Push/POST and expected path is correct then it will return
        the path and request body posted by SAS Under Test or else it will give
        HTTP 404 error."""

  @abc.abstractmethod
  def getBaseUrl(self):
    """Http Server interface to get the Base Url of the Http Server
    Returns:
      Base Url of the Server in the form of string containing https://<URL>:<PORT>
    """
    pass

  @abc.abstractmethod
  def StartServer(self):
    """Http Server interface to start the execution of Http Server in separate thread
    (in background)"""
    pass

  @abc.abstractmethod
  def StopServer(self):
    """Http Server interface to stop the execution of Http Server"""