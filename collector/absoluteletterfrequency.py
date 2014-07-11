from __future__ import absolute_import
import collections
from . import ItemCollector


class ItemLetterAbsoluteFrequencyCollector(ItemCollector):
  def __init__(self, previous_collector_set=None):
    ItemCollector.__init__(self, previous_collector_set)
    self.absolute_letter_frequencies = collections.defaultdict(int)


  def collect(self, item, collector_set=None):
    assert isinstance(item, basestring)
    for c in item:
      self.absolute_letter_frequencies[c] += 1


  def get_result(self, collector_set=None):
    return self.absolute_letter_frequencies
