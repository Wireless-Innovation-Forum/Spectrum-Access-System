import abc
class HttpServerInterface(object):

  @abc.abstractmethod
  def setupFullActivity(self, full_activity_dump=None):
    """

    :param full_activity_dump:
    dict of full activity dump message
    :return: None
    """
    pass

  @abc.abstractmethod
  def setupCbsdActivity(self, unique_id, Cbsd_activity_dump=None):
    """

    :param unique_id: the id to identify cbsd
    :param Cbsd_activity_dump: dict of cbsd activity dump
    :return: None
    """
    pass

  @abc.abstractmethod
  def setupPpaActivity(self, unique_id, PPA_activity_dump=None):
    """
    :param unique_id: the id to identify ppa
    :param PPA_activity_dump: dict of ppa activity dump
    :return: None
    """
    pass

  @abc.abstractmethod
  def setupEscActivity(self, unique_id, esc_activity_dump=None):
    """

    :param unique_id: the id to identify esc
    :param esc_activity_dump: dict of esc activity dump
    :return: None
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