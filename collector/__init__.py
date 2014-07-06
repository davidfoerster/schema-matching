from __future__ import print_function
import utilities, itertools, operator

if __debug__:
  import sys


class ItemCollector(object):
  """Base class for collecting information about a column"""


  def __init__(self, previous_collector_set = None):
    """Initialises a new collector from a set of collectors of a previous phase.
    This may be relevant for some derived collectors.
    """
    object.__init__(self)


  dependencies = ()


  def collect(self, item, collector_set):
    """Called for every item in a column.

    Dependencies are guaranteed to have collected the same item before this collector.
    Override this in subclasses.
    """
    pass


  def get_result(self, collector_set):
    """Returns the result of this collector after all items have been collected."""
    return NotImplemented


  def distance(self, other):
    """Returns the distance between the results of two collector of the same class.

    For simplicity the base implementation assumes that the collector results are numeric.
    """
    assert self.__class__ is other.__class__
    return abs(self.get_result() - other.get_result())


  def __str__(self):
    return str(self.get_result())



class ItemCollectorSet(ItemCollector, dict):
  """Manages a set of collectors for a single column"""

  def __init__(self, collectors = (), predecessor = None):
    ItemCollector.__init__(self)
    dict.__init__(self)
    self.predecessor = predecessor
    self.__semiordered_keylist = list()
    utilities.each(self.add, collectors)


  def collect(self, item, collector_set = None):
    assert collector_set is self
    ItemCollector.collect(self, item, self)
    utilities.each(
      lambda collector: collector.collect(item, self),
      map(self.__getitem__, self.__semiordered_keylist))


  def get_result(self, collector_set = None):
    assert collector_set is None
    return (collector.get_result(self) for collector in self.itervalues())


  def __str__(self):
    return '{{{}}}'.format(', '.join(
      ('{}: {}'.format(cls.__name__, collector) for cls, collector in self.iteritems())))


  def add(self, collector):
    """Adds an item collector and all its dependencies to this set with its type a key,
    if one of the same type isn't in the set already.

    Returns the collector the same type from this set, possibly the one just added.
    """
    if isinstance(collector, type):
      collector = collector(self.predecessor)

    utilities.each(self.add, collector.dependencies)
    result = self.setdefault(collector.__class__, collector)
    if result is collector:
      self.__semiordered_keylist.append(collector.__class__)
      assert len(self.__semiordered_keylist) == len(self)
      assert len(self) == len(set(self.__semiordered_keylist))
    return result



class RowCollector(list):
  """Manages collectors for a set of rows"""

  def collect(self, items):
    """Collects the data of all columns of a row"""
    if __debug__ and len(self) != len(items):
      print('Row has {} columns, expected {}: {}'.format(len(items), len(self), items), file=sys.stderr)

    assert len(self) <= len(items)
    utilities.each_unpack(lambda collector, item: collector.collect(item, collector), itertools.izip(self, items))


  def get_transformer(self):
    item_transformers = tuple(filter(lambda i: i[1], enumerate((c.get_transformer() for c in self))))

    def transform(items):
      for i, t in item_transformers:
        items[i] = t(items[i])

    return transform


  def __str__(self):
    return '({})'.format(', '.join(map(str, self)))



class MultiphaseCollector(object):
  """Manages a sequence of collection phases"""

  def __init__(self, rowset):
    self.phases = list()
    self.rowset = rowset if isinstance(rowset, tuple) else tuple(rowset)
    #assert operator.eq(*utilities.minmax(map(len, self.rowset)))


  def do_phase(self, *collectors):
    predecessors = self.phases[-1] if self.phases else itertools.repeat(None, self.rowset[0])
    phase = RowCollector((ItemCollectorSet(collectors, predecessor) for predecessor in predecessors))
    phase.collect(self.rowset)
    self.phases.append(phase)
