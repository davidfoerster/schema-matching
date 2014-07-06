import math
from collector import ItemCollector
from collector.average import ItemAverageCollector
from collector.count import ItemCountCollector


class ItemVarianceCollector(ItemCollector):

  dependencies = (ItemCountCollector,)


  def __init__(self, previous_collector_set):
    ItemCollector.__init__(self, previous_collector_set)
    self.average = previous_collector_set[ItemAverageCollector].get_result()
    self.sum_of_squares = 0


  def collect(self, item, collector_set=None):
    try:
      value = int(item)
    except ValueError:
      try:
        value = float(item)
      except ValueError:
        return

    self.sum_of_squares += (value - self.average)**2


  def get_result(self, collector_set):
    return self.sum_of_squares / collector_set[ItemCountCollector].get_result()
