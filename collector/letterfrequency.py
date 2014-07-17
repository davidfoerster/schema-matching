from __future__ import absolute_import
from .base import ItemCollector
from utilities.distribution import SparseDistributionTable

if __debug__:
  from utilities.string import basestring



class LetterFrequencyCollector(ItemCollector):

  def __init__(self, previous_collector_set=None):
    ItemCollector.__init__(self, previous_collector_set)
    self.frequencies = SparseDistributionTable(int)


  def collect(self, item, collector_set=None):
    assert isinstance(item, basestring)
    for c in item:
      self.frequencies[c] += 1


  def get_result(self, collector_set=None):
    return self.frequencies


  def as_str(self, collector_set=None, number_fmt=''):
    return format(self.get_result(collector_set), number_fmt)
