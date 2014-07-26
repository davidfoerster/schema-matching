import copy



class ItemCollector(object):
  """Base class for collecting information about a column"""


  def __init__(self, previous_collector_set = None):
    """Initialises a new collector from a set of collectors of a previous phase.
    This may be relevant for some derived collectors.
    """
    super().__init__()
    self.isdependency = False
    self.__has_collected = False
    self.__has_transformed = False


  pre_dependencies = ()

  result_dependencies = ()


  @staticmethod
  def get_instance(template, *args):
    if template is None:
      return None
    if isinstance(template, ItemCollector):
      return copy.copy(template)
    else:
      return template(*args)


  def get_transformer(self):
    return None


  def collect(self, item, collector_set):
    """Called for every item in a column.

    Dependencies are guaranteed to have collected the same item before this collector.
    Override this in subclasses.
    """
    pass


  def get_result(self, collector_set):
    """Returns the result of this collector after all items have been collected."""
    return NotImplemented


  @property
  def has_collected(self): return self.__has_collected
  def set_collected(self): self.__has_collected = True

  @property
  def has_transformed(self): return self.__has_transformed
  def set_transformed(self): self.__has_transformed = True


  @staticmethod
  def result_norm(a, b, *args):
    return abs(a - b)


  @classmethod
  def get_type(cls, collector_set):
    return cls


  def as_str(self, collector_set, format_spec=''):
    return format(self.get_result(collector_set), format_spec)


  def __str__(self):
    return self.as_str(None)
