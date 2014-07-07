from __future__ import division
from math import isnan
from collector import ItemCollector
from collector.average import ItemAverageCollector


class ItemVarianceCollector(ItemCollector):
  def __init__(self, previous_collector_set):
    ItemCollector.__init__(self, previous_collector_set)
    self.average = previous_collector_set[ItemAverageCollector].get_result()
    self.sum_of_squares = 0
    self.sum_of_squares_count = 0


  def collect(self, item, collector_set=None):
    if not isnan(item):
      self.sum_of_squares += (item - self.average) ** 2
      self.sum_of_squares_count += 1


  def get_result(self, collector_set):
    return self.sum_of_squares / self.sum_of_squares_count
