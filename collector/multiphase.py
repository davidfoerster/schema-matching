from __future__ import absolute_import, print_function, division
import copy, collections
import utilities.iterator as uiterator
from itertools import filterfalse, zip_longest, islice, chain
from functools import partial as partialfn
from utilities.iterator import each, consume
from utilities.functional import memberfn, composefn

from .base import ItemCollector
from .tag import TagCollector
from .set import ItemCollectorSet
from .rows import RowCollector
from .itemcount import ItemCountCollector
from .columntype import ColumnTypeItemCollector

if __debug__:
  import operator



class MultiphaseCollector(object):
  """Manages a sequence of collection phases"""

  def __init__(self, rowset, name=None):
    self.name = name
    self.rowset = rowset if isinstance(rowset, collections.Sequence) else tuple(rowset)
    #assert operator.eq(*utilities.minmax(map(len, self.rowset)))
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
            add_copy_and_dependencies(predecessor[dep], True)
          if isdependency is None:
            isdependency = collector.isdependency
          collector = ics.setdefault(type(collector), copy.copy(collector))
          collector.isdependency &= isdependency

        each(memberfn(add_copy_and_dependencies, None),
          filter(keep, predecessor.values()))
        yield ics
    else:
      for _ in range(len(self.rowset[0])):
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
        for ctype, coll in coll_set.items():
          assert coll.isdependency is (ctype not in independent)

    return phase_count


  def __gen_itemcollector_sets(self, phase_desc):
    return (
      pred if desc is None else ItemCollectorSet(desc.values(), pred)
      for desc, pred in zip(phase_desc, self.merged_predecessors))


  @staticmethod
  def __contains_factory(phase_desc):
    return not all((
      isinstance(ctype, ItemCollector) or
        (type(ctype) is type and issubclass(ctype, ItemCollector))
      for ctype in chain(*filter(None, phase_desc))))


  def get_phase_descriptions(self, collector_descriptions):
    # column-first ordering
    phase_descriptions = map(
      partialfn(self.__get_dependency_chain, collector_descriptions),
      self.merged_predecessors)
    # transpose to phase-first ordering
    phase_descriptions = zip_longest(*phase_descriptions)
    return phase_descriptions


  def __get_dependency_chain(self, collector_descriptions, predecessors=None):
    """
    Returns a list of phase-wise collector descriptions for a single column.

    :param collector_descriptions: iterable
    :param predecessors: ItemCollectorSet
    :return: list[dict]
    """
    phase = dict(filterfalse(
      lambda item: item[0] is None or item[0] in predecessors,
      ((template.get_type(predecessors), template)
        for template in collector_descriptions)))
    independent = TagCollector('independent', frozenset(phase.keys()), True)

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
        for dep in filterfalse(predecessors.__contains__, template.pre_dependencies):
          phase_pre_dependencies.setdefault(dep, dep)
          collector_min_phases[dep] = len(phases) - 1
      else:
        for dep in filter(must_add_dependency, template.result_dependencies):
          add_dependencies(dep)
          phase_result_dependencies.add(dep)

    # resolve dependencies and push them to an earlier phase
    while phase:
      phase_pre_dependencies = dict()
      phase_result_dependencies.clear()
      each(add_dependencies, phase.keys())
      phases.append(phase)
      phase = phase_pre_dependencies

    # remove later duplicates
    consume((
      each(memberfn(dict.pop, ctype, None), islice(phases, 0, -min_phase_idx))
      for ctype, min_phase_idx in collector_min_phases.items()))

    if predecessors is not None:
      predecessors[independent] = independent
    elif phases:
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
