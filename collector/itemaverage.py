from __future__ import division
from collector import ItemCollector
from collector.itemsum import ItemSumCollector
from collector.itemcount import ItemCountCollector


class ItemAverageCollector(ItemCollector):

  result_dependencies = (ItemCountCollector, ItemSumCollector)

  def __init__(self, previous_collector_set = None):
    ItemCollector.__init__(self, previous_collector_set)


  def get_result(self, collector_set):
    sumcoll = collector_set[ItemSumCollector]
    return (sumcoll.get_result() /
      (collector_set[ItemCountCollector].get_result() - sumcoll.type_error_count))
