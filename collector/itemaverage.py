from __future__ import division
from math import expm1
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



def normalize(x):
  """
  Returns
     -(exp(-x) - 1)
   = -(exp(-x) - 1)
   = 1 - exp(-x)

  This gives us a nicely normalised distance measure that penalises large
  values subproportionally.
  """
  return -expm1(-x)
