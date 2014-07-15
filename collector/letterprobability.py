from __future__ import absolute_import, division
import utilities.string
from . import ItemCollector
from .lettercount import ItemLetterCountCollector
from .letterfrequency import LetterFrequencyCollector


class LetterProbablilityCollector(ItemCollector):

  result_dependencies = (ItemLetterCountCollector, LetterFrequencyCollector)


  def __init__(self, previous_collector_set):
    ItemCollector.__init__(self, previous_collector_set)
    self.__cached_result = None


  def get_result(self, collector_set):
    if self.__cached_result is None:
      self.__cached_result = \
        collector_set[LetterFrequencyCollector].get_result(collector_set) \
          .normalize(collector_set[ItemLetterCountCollector].get_result(collector_set))
    return self.__cached_result


  def as_str(self, collector_set, number_fmt=''):
    return format(self.get_result(collector_set), number_fmt)


  @staticmethod
  def result_norm(a, b):
    return a.distance_to(b)
