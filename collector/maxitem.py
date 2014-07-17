from .base import ItemCollector
from utilities import infinity



class MaxItemCollector(ItemCollector):

  def __init__(self, previous_collector_set = None):
    ItemCollector.__init__(self, previous_collector_set)
    self.max = -infinity


  def collect(self, item, collector_set = None):
    if item is not None and item > self.max:
      self.max = item


  def get_result(self, collector_set = None):
    return self.max
