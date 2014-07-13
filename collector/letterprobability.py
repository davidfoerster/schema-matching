from __future__ import absolute_import, division
import utilities.string
from . import ItemCollector
from .lettercount import ItemLetterCountCollector
from .letterfrequency import LetterFrequencyCollector


class LetterProbabliityCollector(ItemCollector):

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
    return u'({})'.format(u', '.join((
      u'{}: {:{}}'.format(utilities.string.char_repr(char), frequency, number_fmt)
      for char, frequency in self.get_result(collector_set).iteritems())))


  @staticmethod
  def result_norm(a, b):
    return a.distance_to(b)
