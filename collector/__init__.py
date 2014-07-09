from __future__ import print_function
import os, utilities, itertools, copy, collections

if __debug__:
  import operator

verbosity = os.getenv('VERBOSE', '')
try:
  verbosity = int(verbosity if verbosity else __debug__)
except ValueError:
  import sys
  print('Warning: Environment variable VERBOSE has unparsable, invalid content:', verbosity, file = sys.stderr)
  verbosity = int(__debug__)
else:
  if verbosity >= 1:
    import sys



class ItemCollector(object):
  """Base class for collecting information about a column"""


  def __init__(self, previous_collector_set = None):
    """Initialises a new collector from a set of collectors of a previous phase.
    This may be relevant for some derived collectors.
    """
    object.__init__(self)
    self.isdependency = False


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


  @staticmethod
  def result_norm(a, b):
    return abs(a - b)


  def as_str(self, collector_set):
    return str(self.get_result(collector_set))


  def __str__(self):
    return self.as_str(None)



class ItemCollectorSet(ItemCollector, collections.OrderedDict):
  """Manages a set of collectors for a single column"""

  def __init__(self, collectors = (), predecessor = None):
    ItemCollector.__init__(self)
    collections.OrderedDict.__init__(self)
    self.predecessor = predecessor
    utilities.each(self.add, collectors)


  def collect(self, item, collector_set = None):
    assert collector_set is self
    ItemCollector.collect(self, item, self)
    utilities.each(
      lambda collector: collector.collect(item, self),
      self.itervalues())


  class __result_type(object):

    def __init__(self, collector_set):
      object.__init__(self)
      self.__collector_set = collector_set

    def __iter__(self):
      collector_set = self.__collector_set
      return (c.get_result(collector_set) for c in collector_set.itervalues())

    def __cmp__(self, other, weights = None):
      assert isinstance(other, type(self))
      a = self.__collector_set
      b = other.__collector_set
      if not utilities.issubset(a.iterkeys(), b):
        return None

      def distance_of_unweighted(a_coll):
        assert a[type(a_coll)] is a_coll
        return abs(a_coll.result_norm(a_coll.get_result(a), b[type(a_coll)].get_result(b)))

      if weights is None:
        distance_of = distance_of_unweighted
      else:
        def distance_of(a_coll):
          d = distance_of_unweighted(a_coll)
          w = weights[type(a_coll)]
          return w(d) if callable(w) else w * d

      return sum((distance_of(coll) for coll in a.itervalues() if not coll.isdependency))


  def get_result(self, collector_set = None):
    assert collector_set is None
    return ItemCollectorSet.__result_type(self)


  result_norm = __result_type.__cmp__


  def get_transformer(self):
    for t in itertools.ifilter(None, (c.get_transformer() for c in self.itervalues())):
      return t
    return None


  def as_str(self, collector_set=None):
    assert collector_set is None
    return '{{{}}}'.format(', '.join(
      ('{}: {}'.format(type(collector).__name__, collector.as_str(self))
        for collector in self.itervalues()
        if not collector.isdependency)))


  def add(self, collector, isdependency = False):
    """Adds an item collector and all its result_dependencies to this set with its type a key,
    if one of the same type isn't in the set already.

    Returns the collector the same type from this set, possibly the one just added.
    """
    collector = ItemCollector.get_instance(collector, self.predecessor)
    if not collector:
      return None

    utilities.each(self.__add_dependency, collector.result_dependencies)
    collector = self.setdefault(type(collector), collector)
    collector.isdependency |= isdependency
    return collector


  def __add_dependency(self, collector):
    return self.add(collector, True)



class RowCollector(list):
  """Manages collectors for a set of rows"""

  def reset(self, collectors):
    self[:] = collectors


  def collect(self, items):
    """Collects the data of all columns of a row"""
    if verbosity >= 2 and len(self) != len(items):
      print('Row has {} columns, expected {}: {}'.format(len(items), len(self), items), file = sys.stderr)

    assert len(self) <= len(items)
    utilities.each_unpack(lambda collector, item: collector.collect(item, collector), itertools.izip(self, items))


  def collect_all(self, rows):
    utilities.each(self.collect, rows)


  class __transformer(tuple):

    def __call__(self, items):
      for i, t in self:
        items[i] = t(items[i])


  def get_transformer(self):
    return self.__transformer(itertools.ifilter(utilities.second,
      enumerate(itertools.imap(utilities.apply_memberfn('get_transformer'), self))))


  def transform_all(self, rows):
    utilities.each(self.get_transformer(), rows)


  def results_norms(a, b):
    # Materialise results of inner loop because they'll be scanned multiple times.
    resultsA = [coll.get_result() for coll in a]
    resultsB = (coll.get_result() for coll in b)
    return [
      [collB.result_norm(resultA, resultB) for resultA in resultsA]
      for collB, resultB in itertools.izip(b, resultsB)
    ]


  def __str__(self):
    return '({})'.format(', '.join(itertools.imap(str, self)))



class MultiphaseCollector(object):
  """Manages a sequence of collection phases"""

  def __init__(self, rowset):
    self.rowset = rowset if isinstance(rowset, tuple) else tuple(rowset)
    #assert operator.eq(*utilities.minmax(itertools.imap(len, self.rowset)))
    self.merged_predecessors = itertools.repeat(None, len(self.rowset[0]))


  def __call__(self, *collectors):
    phase = RowCollector((ItemCollectorSet(collectors, predecessor) for predecessor in self.merged_predecessors))
    phase.collect_all(self.rowset)
    phase.transform_all(self.rowset)

    if isinstance(self.merged_predecessors, RowCollector):
      utilities.each_unpack(ItemCollectorSet.update, itertools.izip(self.merged_predecessors, phase))
    else:
      self.merged_predecessors = phase


  def results_norms(a, b):
    """
    :param a: self
    :param b: MultiphaseCollector
    :return: list[list[float]]
    """
    return a.merged_predecessors.results_norms(b.merged_predecessors)
