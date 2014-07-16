from __future__ import absolute_import, print_function, division
import collections, math
import os, copy, inspect
from .weight import WeightDict
import utilities
import utilities.iterator as uiterator
import utilities.operator as uoperator
from itertools import imap, ifilter, ifilterfalse, izip, izip_longest, islice, chain
from functools import partial as partialfn
from utilities.iterator import each, consume
from utilities.functional import memberfn, composefn
from utilities.string import join

if __debug__:
  import operator


verbosity = os.getenv('VERBOSE', '')
try:
  verbosity = int(verbosity or __debug__)
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
  def result_norm(a, b):
    return abs(a - b)


  @classmethod
  def get_type(cls, collector_set):
    return cls


  def as_str(self, collector_set, format_spec=''):
    return format(self.get_result(collector_set), format_spec)


  def __str__(self):
    return self.as_str(None)



class TagCollector(ItemCollector):

  def __init__(self, id, data=None):
    ItemCollector.__init__(self)
    self.set_collected()
    self.set_transformed()
    self.__id = id
    self.data = data


  @property
  def id(self):
    return self.__id


  def as_str(self, collector_set, format_spec=None):
    return join(str(self.__id), ': ', str(self.data))


  def __eq__(self, other):
    return (self.__id == other or
      (isinstance(other, TagCollector) and self.__id == other.__id))


  def __ne__(self, other): return not self.__eq__(other)

  def __hash__(self): return hash(self.__id)

  def get_result(self, collector_set): return None

  def get_type(self, collector_set): return self



class ItemCollectorSet(ItemCollector, collections.OrderedDict):
  """Manages a set of collectors for a single column"""

  def __init__(self, collectors = (), predecessor = None):
    ItemCollector.__init__(self)
    collections.OrderedDict.__init__(self)

    self.predecessor = predecessor
    if predecessor:
      assert all(imap(memberfn(getattr, 'has_collected'), predecessor.itervalues()))
      self.update(predecessor)
    each(self.add, collectors)


  def collect(self, item, collector_set = None):
    assert collector_set is self
    collect = ItemCollector.collect
    collect(self, item, self)
    each(memberfn('collect', item, self),
      ifilterfalse(memberfn(getattr, 'has_collected'),
        self.itervalues()))


  class __result_type(object):

    def __init__(self, collector_set):
      object.__init__(self)
      self.__collector_set = collector_set

    def __iter__(self):
      collector_set = self.__collector_set
      return (c.get_result(collector_set) for c in collector_set.itervalues())

    def __cmp__(self, other, weights = WeightDict()):
      assert isinstance(other, type(self))
      a = self.__collector_set
      b = other.__collector_set
      if not utilities.issubset(a.iterkeys(), b):
        return weights[ItemCollectorSet].for_infinity

      def distance_of_unweighted(a_coll):
        assert a[type(a_coll)] is a_coll and type(b[type(a_coll)]) is type(a_coll)
        return a_coll.result_norm(
          a_coll.get_result(a), b[type(a_coll)].get_result(b))

      weight_sum = utilities.NonLocal(0)
      if weights is None:
        def distance_of(a_coll):
          weight_sum.value += 1
          return distance_of_unweighted(a_coll)
      else:
        def distance_of(a_coll):
          weight = weights[type(a_coll)]
          weight_sum.value += weight.for_infinity
          return weight(distance_of_unweighted(a_coll))

      value_sum = weights.sum((
        distance_of(coll) for coll in a.itervalues() if not coll.isdependency))
      if value_sum:
        assert weight_sum.value > 0
        assert not 'normalized' in weights.tags or math.fabs(value_sum / weight_sum.value) <= 1.0
        return value_sum / weight_sum.value
      else:
        return utilities.NaN


  def set_collected(self): self.__forward_call()

  def set_transformed(self): self.__forward_call()


  def __forward_call(self, fn_name=None, *args):
    if fn_name is None:
      fn_name = inspect.stack()[1][3]
    each(memberfn(fn_name, *args), self.itervalues())
    getattr(super(ItemCollectorSet, self), fn_name)(*args)


  def get_result(self, collector_set = None):
    assert collector_set is None
    return ItemCollectorSet.__result_type(self)


  result_norm = __result_type.__cmp__


  def get_transformer(self):
    transformer = composefn(*ifilter(None,
      imap(memberfn('get_transformer'),
        ifilterfalse(memberfn(getattr, 'has_transformed'),
          self.itervalues()))))
    return None if transformer is uoperator.identity else transformer


  def as_str(self, collector_set=None, format_spec=''):
    assert collector_set is None
    return join('{', u', '.join((
        join(type(collector).__name__, ': ', collector.as_str(self, format_spec))
        for collector in self.itervalues() if not collector.isdependency)),
      '}')


  def __format__(self, format_spec=''): return self.as_str(None, format_spec)


  def __str__(self): return self.as_str()


  def add(self, template, isdependency=False):
    """Adds an item collector and all its result_dependencies to this set with its type a key,
    if one of the same type isn't in the set already.

    Returns the collector the same type from this set, possibly the one just added.
    """
    collector_type = template.get_type(self.predecessor)
    collector = self.get(collector_type)

    if collector is None:
      collector = ItemCollector.get_instance(template, self.predecessor)
      if not isinstance(collector, ItemCollector):
        assert collector is None
        return None
      collector.isdependency = isdependency
      each(self.__add_dependency, collector.result_dependencies)
      collector = self.setdefault(collector_type, collector)

    collector.isdependency &= isdependency
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
    each(self.__collect_column, self, items)


  @staticmethod
  def __collect_column(collector, item):
    collector.collect(item, collector)


  def collect_all(self, rows):
    each(self.collect, rows)
    each(memberfn('set_collected'), self)


  class __transformer(tuple):

    def __call__(self, items):
      for i, t in self:
        items[i] = t(items[i])


  def get_transformer(self):
    column_transformers = tuple(
      ifilter(uoperator.second,
        enumerate(imap(memberfn('get_transformer'), self))))

    if column_transformers:
      def row_transformer(items):
        for column_idx, column_transformer in column_transformers:
          items[column_idx] = column_transformer(items[column_idx])
    else:
      row_transformer = None

    return row_transformer


  def transform_all(self, rows):
    transformer = self.get_transformer()
    if transformer is not None:
      each(transformer, rows)
      each(memberfn('set_transformed'), self)


  def results_norms(a, b, weights=None):
    get_result = memberfn('get_result')
    # Materialise results of inner loop because they'll be scanned multiple times.
    resultsA = map(get_result, a)
    resultsB = imap(get_result, b)
    return [
      [collB.result_norm(resultA, resultB, weights) for resultA in resultsA]
      for collB, resultB in izip(b, resultsB)
    ]


  def as_str(self, format_spec=''):
    return join('(', u', '.join(imap(memberfn('as_str', None, format_spec), self)), ')')


  def __str__(self): return self.as_str()

  __format__ = as_str



from .itemcount import ItemCountCollector
from .columntype import ColumnTypeItemCollector


class MultiphaseCollector(object):
  """Manages a sequence of collection phases"""

  def __init__(self, rowset, name=None):
    self.name = name
    self.rowset = rowset if isinstance(rowset, collections.Sequence) else tuple(rowset)
    #assert operator.eq(*utilities.minmax(itertools.imap(len, self.rowset)))
    self.reset(None)


  def reset(self, keep=(ItemCountCollector, ColumnTypeItemCollector)):
    self.merged_predecessors = RowCollector(self.__emit_itemcollector_set(keep))
    return self


  def __emit_itemcollector_set(self, keep):
    if keep and isinstance(self.merged_predecessors, RowCollector):
      keep = composefn(type, keep.__contains__)
      for predecessor in self.merged_predecessors:
        ics = ItemCollectorSet()

        def add_copy_and_dependencies(collector, isdependency):
          for dep in collector.result_dependencies: # TODO: Rewrite functionally
            add_copy_and_dependencies(predecessor[type(dep)], True)
          if isdependency is None:
            isdependency = collector.isdependency
          collector = ics.setdefault(type(collector), copy.copy(collector))
          collector.isdependency &= isdependency

        each(memberfn(add_copy_and_dependencies, None),
          ifilter(keep, predecessor.itervalues()))
        yield ics
    else:
      for _ in xrange(len(self.rowset[0])):
        ics = ItemCollectorSet()
        ics.add(ItemCountCollector(len(self.rowset)), True)
        yield ics


  def do_phases(self, collector_descriptions, callback=None):
    phase_count = 0
    while True:
      phase_descriptions = self.get_phase_descriptions(collector_descriptions)
      if __debug__:
        phase_descriptions = tuple(phase_descriptions)

      for phase_description in phase_descriptions:
        if self.__contains_factory(phase_description):
          assert phase_description is not phase_descriptions[0]
          break
        self.__do_phase_magic(self.__gen_itemcollector_sets(phase_description))
        phase_count += 1
        if callback is not None:
          callback(self)
      else:
        break

    if __debug__:
      for coll_set in self.merged_predecessors:
        independent = frozenset((template.get_type(coll_set) for template in collector_descriptions))
        for ctype, coll in coll_set.iteritems():
          assert coll.isdependency is (ctype not in independent)

    return phase_count


  def __gen_itemcollector_sets(self, phase_desc):
    for desc, pred in izip(phase_desc, self.merged_predecessors):
      if desc is None:
        yield pred
      else:
        independent = (desc.get('independent') or pred.get('independent')).data
        ics = ItemCollectorSet((), pred)
        for template in desc.itervalues(): # TODO: Rewrite functionally
          ics.add(template, template not in independent)
        yield ics


  @staticmethod
  def __contains_factory(phase_desc):
    return not all((
      isinstance(ctype, ItemCollector) or
        (type(ctype) is type and issubclass(ctype, ItemCollector))
      for ctype in chain(*ifilter(None, phase_desc))))


  def get_phase_descriptions(self, collector_descriptions):
    # column-first ordering
    phase_descriptions = uiterator.map(
      partialfn(self.__get_dependency_chain, collector_descriptions),
      self.merged_predecessors)
    # transpose to phase-first ordering
    phase_descriptions = izip_longest(*phase_descriptions)
    return phase_descriptions


  def __get_dependency_chain(self, collector_descriptions, predecessors=None):
    """
    Returns a list of phase-wise collector descriptions for a single column.

    :param collector_descriptions: iterable
    :param predecessors: ItemCollectorSet
    :return: list[dict]
    """
    phase = dict(ifilterfalse(
      lambda item: item[0] is None or item[0] in predecessors,
      ((template.get_type(predecessors), template)
        for template in collector_descriptions)))
    for ctype in predecessors.iterkeys():
      phase.pop(ctype, None)
    independent = TagCollector('independent', frozenset(phase.iterkeys()))

    phases = []
    collector_min_phases = dict()
    phase_pre_dependencies = None
    phase_result_dependencies = set()

    def must_add_dependency(dep):
      return (dep not in phase and
        dep not in phase_result_dependencies and
        dep not in phase_pre_dependencies)

    def add_dependencies(template):
      if template.pre_dependencies:
        for dep in ifilterfalse(predecessors.__contains__, template.pre_dependencies):
          phase_pre_dependencies.setdefault(dep, dep)
          collector_min_phases[dep] = len(phases) - 1
      else:
        for dep in ifilter(must_add_dependency, template.result_dependencies):
          add_dependencies(dep)
          phase_result_dependencies.add(dep)

    # resolve dependencies and push them to an earlier phase
    while phase:
      phase_pre_dependencies = dict()
      phase_result_dependencies.clear()
      each(add_dependencies, phase.iterkeys())
      phases.append(phase)
      phase = phase_pre_dependencies

    # remove later duplicates
    consume((
      each(memberfn(dict.pop, ctype, None), islice(phases, 0, -min_phase_idx))
      for ctype, min_phase_idx in collector_min_phases.iteritems()))

    if phases:
      phases[-1][independent] = independent
    return uiterator.filter(None, reversed(phases))


  def do_phase(self, phase_description):
    self.__do_phase_magic((ItemCollectorSet(phase_description, pred)
      for pred in self.merged_predecessors))


  def __do_phase_magic(self, itemcollector_sets):
    phase = RowCollector(itemcollector_sets)
    phase.collect_all(self.rowset)
    phase.transform_all(self.rowset)
    self.merged_predecessors = phase


  __call__ = do_phase


  def results_norms(a, b, weights=None):
    """
    :param a: self
    :param b: MultiphaseCollector
    :return: list[list[float]]
    """
    return a.merged_predecessors.results_norms(b.merged_predecessors, weights)
