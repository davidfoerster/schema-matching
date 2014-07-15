from __future__ import absolute_import, print_function, division
import os, itertools, functools, copy, collections, math
from .weight import WeightDict
import utilities, utilities.string
import utilities.iterator as uiterator
import utilities.functional as ufunctional
import utilities.operator as uoperator

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


  def has_collected(self): return self.__has_collected
  def set_collected(self): self.__has_collected = True


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
    return utilities.string.join(str(self.__id), ': ', str(self.data))


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
      assert all(itertools.imap(ItemCollector.has_collected, predecessor.itervalues()))
      self.update(predecessor)
    uiterator.each(self.add, collectors)


  def collect(self, item, collector_set = None):
    assert collector_set is self
    collect = ItemCollector.collect
    collect(self, item, self)
    uiterator.each(ufunctional.apply_memberfn(collect.__name__, item, self),
      itertools.ifilterfalse(ItemCollector.has_collected, self.itervalues()))


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


  def set_collected(self):
    setter = ItemCollector.set_collected
    uiterator.each(ufunctional.apply_memberfn(setter.__name__),
      self.itervalues())
    setter(self)


  def set_transformed(self):
    setter = ItemCollector.set_transformed
    uiterator.each(ufunctional.apply_memberfn(setter.__name__),
      self.itervalues())
    setter(self)


  def get_result(self, collector_set = None):
    assert collector_set is None
    return ItemCollectorSet.__result_type(self)


  result_norm = __result_type.__cmp__


  def get_transformer(self):
    transformer = ufunctional.composefn(*itertools.ifilter(None,
      itertools.imap(ufunctional.apply_memberfn(ItemCollector.get_transformer.__name__),
        itertools.ifilterfalse(ItemCollector.has_transformed, self.itervalues()))))
    if not transformer.args[1]:
      return None
    if len(transformer.args[1]) == 1:
      return transformer.args[1][0]
    else:
      return transformer


  def as_str(self, collector_set=None, format_spec=''):
    assert collector_set is None
    return utilities.string.join('{', u', '.join(
        (u'{}: {}'.format(type(collector).__name__, collector.as_str(self, format_spec))
          for collector in self.itervalues()
          if not collector.isdependency)),
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
      uiterator.each(self.__add_dependency, collector.result_dependencies)
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
    uiterator.each(self.__collect_column, self, items)


  @staticmethod
  def __collect_column(collector, item):
    collector.collect(item, collector)


  def collect_all(self, rows):
    uiterator.each(self.collect, rows)
    uiterator.each(ufunctional.apply_memberfn(
      ItemCollector.set_collected.__name__), self)


  class __transformer(tuple):

    def __call__(self, items):
      for i, t in self:
        items[i] = t(items[i])


  def get_transformer(self):
    column_transformers = tuple(itertools.ifilter(uoperator.second,
      enumerate(itertools.imap(
        ufunctional.apply_memberfn(ItemCollector.get_transformer.__name__),
        self))))

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
      uiterator.each(transformer, rows)
      uiterator.each(ufunctional.apply_memberfn(
        ItemCollector.set_transformed.__name__), self)


  def results_norms(a, b, weights=None):
    get_result = ufunctional.apply_memberfn('get_result')
    # Materialise results of inner loop because they'll be scanned multiple times.
    resultsA = map(get_result, a)
    resultsB = itertools.imap(get_result, b)
    return [
      [collB.result_norm(resultA, resultB, weights) for resultA in resultsA]
      for collB, resultB in itertools.izip(b, resultsB)
    ]


  def as_str(self, format_spec=''):
    return utilities.string.join('(', u', '.join(
        itertools.imap(ufunctional.apply_memberfn(
          'as_str', None, format_spec), self)),
      ')')


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
      keep = ufunctional.composefn(type, keep.__contains__)
      for predecessor in self.merged_predecessors:
        ics = ItemCollectorSet()

        def add_copy_and_dependencies(collector, isdependency):
          for dep in collector.result_dependencies:
            add_copy_and_dependencies(predecessor[type(dep)], True)
          if isdependency is None:
            isdependency = collector.isdependency
          collector = ics.setdefault(type(collector), copy.copy(collector))
          collector.isdependency &= isdependency

        for collector in itertools.ifilter(keep, predecessor.itervalues()):
          add_copy_and_dependencies(collector, None)
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
    for desc, pred in itertools.izip(phase_desc, self.merged_predecessors):
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
      for ctype in itertools.chain(*itertools.ifilter(None, phase_desc))))


  def get_phase_descriptions(self, collector_descriptions):
    # column-first ordering
    phase_descriptions = uiterator.map(
      functools.partial(self.__get_dependency_chain, collector_descriptions),
      self.merged_predecessors)
    # transpose to phase-first ordering
    phase_descriptions = itertools.izip_longest(*phase_descriptions)
    return phase_descriptions


  def __get_dependency_chain(self, collector_descriptions, predecessors=None):
    """
    Returns a list of phase-wise collector descriptions for a single column.

    :param collector_descriptions: iterable
    :param predecessors: ItemCollectorSet
    :return: list[dict]
    """
    phase = {template.get_type(predecessors): template
      for template in collector_descriptions}
    phase.pop(None, None)
    independent = TagCollector('independent', set(phase.iterkeys()))
    for ctype in predecessors.iterkeys():
      phase.pop(ctype, None)

    phases = []
    collector_min_phases = dict()
    phase_pre_dependencies = None
    phase_result_dependencies = set()
    current_phase_idx = 1 # Phases will have negative indices starting from zero since we're building them from the back; TODO: probably unnecessary

    def add_dependencies(template, phase_idx):
      if template.pre_dependencies:
        for dep in template.pre_dependencies: # TODO: Rewrite functionally
          if not dep in predecessors:
            phase_pre_dependencies.setdefault(dep, dep)
            assert phase_idx - 1 <= collector_min_phases.get(dep, 0)
            collector_min_phases[dep] = phase_idx - 1
      else:
        for dep in template.result_dependencies: # TODO: Rewrite functionally
          if dep not in phase and dep not in phase_result_dependencies and dep not in phase_pre_dependencies:
            add_dependencies(dep, phase_idx)
            phase_result_dependencies.add(dep)

    # resolve dependencies and push them to an earlier phase
    while phase:
      current_phase_idx -= 1
      phases.append(phase)
      phase_pre_dependencies = dict()
      phase_result_dependencies.clear()

      for ctype in phase.iterkeys(): # TODO: Rewrite functionally
        add_dependencies(ctype, current_phase_idx)
         # TODO: Does this ever happen?
        assert current_phase_idx >= collector_min_phases.get(ctype, 0)
        if current_phase_idx < collector_min_phases.get(ctype, 0):
          collector_min_phases[ctype] = current_phase_idx

      phase = phase_pre_dependencies

    # remove later duplicates
    for ctype, min_phase_idx in collector_min_phases.iteritems(): # TODO: Rewrite functionally
      for phase in itertools.islice(phases, 0, -min_phase_idx):
        phase.pop(ctype, None)

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
