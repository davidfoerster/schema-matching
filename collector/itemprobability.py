from __future__ import absolute_import, division
import utilities.string
from . import ItemCollector
from .lettercount import ItemLetterCountCollector
from .absoluteletterfrequency import ItemLetterAbsoluteFrequencyCollector


class ItemLetterRelativeFrequencyCollector(ItemCollector):

  result_dependencies = (ItemLetterCountCollector, ItemLetterAbsoluteFrequencyCollector)


  def __init__(self, previous_collector_set):
    ItemCollector.__init__(self, previous_collector_set)
    self.__cached_result = None


  def get_result(self, collector_set):
    if self.__cached_result is None:
      self.__cached_result = \
        collector_set[ItemLetterAbsoluteFrequencyCollector].get_result(collector_set) \
          .normalise(collector_set[ItemLetterCountCollector].get_result(collector_set))
    return self.__cached_result


  def as_str(self, collector_set, number_fmt=''):
    return u'({})'.format(u', '.join((
      u'{}: {:{}}'.format(utilities.string.char_repr(char), frequency, number_fmt)
      for char, frequency in self.get_result(collector_set))))


  @staticmethod
  def result_norm(a, b):
    return a.distance_to(b)
