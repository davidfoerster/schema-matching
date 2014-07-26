from .base import ItemCollector
from .itemsum import ItemSumCollector
from .itemcount import ItemCountCollector



class ItemAverageCollector(ItemCollector):

  result_dependencies = (ItemCountCollector, ItemSumCollector)

  def __init__(self, previous_collector_set = None):
    super().__init__(previous_collector_set)


  def get_result(self, collector_set):
    sumcoll = collector_set[ItemSumCollector]
    return (sumcoll.get_result() /
      (collector_set[ItemCountCollector].get_result() - sumcoll.type_error_count))
