from __future__ import absolute_import
import collections
from . import ItemCollector


class ItemFrequencyCollector(ItemCollector):

  def __init__(self, previous_collector_set=None):
    ItemCollector.__init__(self, previous_collector_set)
    self.absolute_frequencies = collections.defaultdict(int)


  def collect(self, item, collector_set=None):
    self.absolute_frequencies[item] += 1


  def get_result(self, collector_set=None):
    return self.absolute_frequencies