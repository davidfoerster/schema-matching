import utilities, itertools


class ItemCollector(object):
  """Base class for collecting information about a column"""


  def dependencies(self):
    """Return collector types this collector depends on"""
    return ()


  def collect(self, item, collector_set = None):
    """Called for every item in a column. Override this in subclasses."""
    pass


  def get_result(self, collector_set = None):
    """Returns the result of this collector after all items have been collected."""
    return NotImplemented



class ItemCollectorSet(ItemCollector, dict):
  """Manages a set of collectors for a single column"""

  def __init__(self, *args):
    ItemCollector.__init__(self)
    dict.__init__(self)
    self.__semiordered_keylist = list()
    utilities.each(self.add, args)


  def collect(self, item, collector_set = None):
    assert collector_set is None
    ItemCollector.collect(self, item, self)
    utilities.each(
      lambda collector: collector.collect(item, self),
      map(self.__getitem__, self.__semiordered_keylist))


  def get_result(self, collector_set = None):
    assert collector_set is None
    return (collector.get_result(self) for collector in self.itervalues())


  def add(self, collector):
    """Adds an item collector and all its dependencies to this set with its type a key,
    if one of the same type isn't in the set already.

    Returns the collector the same type from this set, possibly the one just added.
    """
    if isinstance(collector, type):
      collector = collector()

    utilities.each(self.add, collector.dependencies())
    result = self.setdefault(collector.__class__, collector)
    if result is collector:
      self.__semiordered_keylist.append(collector.__class__)
      assert len(self.__semiordered_keylist) == len(self)
      assert len(self) == len(set(self.__semiordered_keylist))
    return result



class RowCollector(list):
  """Manages collectors for a set of rows"""

  def collect(self, *items):
    """Collects the data of all columns of a row"""
    assert len(self) == len(items)
    utilities.each(lambda collector, item: collector.collect(item), itertools.izip(self, items))
