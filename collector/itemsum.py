from math import isnan
from . import ItemCollector


class ItemSumCollector(ItemCollector):

  def __init__(self, previous_collector_set = None):
    ItemCollector.__init__(self, previous_collector_set)
    self.sum = 0
    self.type_error_count = 0


  def collect(self, item, collector_set = None):
    try:
      if not isnan(item):
        self.sum += item
    except TypeError:
      self.type_error_count += 1


  def get_result(self, collector_set = None):
    return self.sum
