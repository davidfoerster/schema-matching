from __future__ import absolute_import
from .base import ItemCollector
from utilities import infinity



class MinItemCollector(ItemCollector):

  def __init__(self, previous_collector_set = None):
    ItemCollector.__init__(self, previous_collector_set)
    self.min = infinity


  def collect(self, item, collector_set = None):
    if item is not None and item < self.min:
      self.min = item


  def get_result(self, collector_set = None):
    return self.min
