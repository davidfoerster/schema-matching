from __future__ import division, absolute_import
from math import isnan, sqrt
from . import ItemCollector
from .itemaverage import ItemAverageCollector


class ItemVarianceCollector(ItemCollector):

  def __init__(self, previous_collector_set):
    ItemCollector.__init__(self, previous_collector_set)
    self.average = \
      previous_collector_set[ItemAverageCollector]. \
        get_result(previous_collector_set)
    self.sum_of_squares = 0
    self.sum_of_squares_count = 0


  def collect(self, item, collector_set=None):
    try:
      if not isnan(item):
        self.sum_of_squares += (item - self.average) ** 2
        self.sum_of_squares_count += 1
    except TypeError:
      pass


  def get_result(self, collector_set = None):
    return self.sum_of_squares / self.sum_of_squares_count



class ItemStandardDeviationCollector(ItemCollector):

  result_dependencies = (ItemVarianceCollector,)

  def get_result(self, collector_set):
    return sqrt(collector_set[ItemVarianceCollector].get_result(collector_set))



class ItemVariationCoefficientCollector(ItemCollector):

  result_dependencies = (ItemVarianceCollector,)

  def get_result(self, collector_set = None):
    varcoll = collector_set[ItemVarianceCollector]
    return sqrt(varcoll.get_result()) / varcoll.average
