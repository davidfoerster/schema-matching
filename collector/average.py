from __future__ import division
from collector import ItemCollector
from collector.sum import ItemSumCollector
from collector.count import ItemCountCollector


class ItemAverageCollector(ItemCollector):

  dependencies = (ItemCountCollector, ItemSumCollector)

  def __init__(self, previous_collector_set = None):
    ItemCollector.__init__(self, previous_collector_set)


  def get_result(self, collector_set):
    return collector_set[ItemSumCollector].get_result() / collector_set[ItemCountCollector].get_result()
