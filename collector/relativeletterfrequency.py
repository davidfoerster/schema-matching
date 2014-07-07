from __future__ import division
import utilities
from collector import ItemCollector
from collector.lettercount import ItemLetterCountCollector
from collector.absoluteletterfrequency import ItemLetterAbsoluteFrequencyCollector


class ItemLetterRelativeFrequencyCollector(ItemCollector):

  result_dependencies = (ItemLetterAbsoluteFrequencyCollector,)


  def __init__(self, previous_collector_set):
    ItemCollector.__init__(self, previous_collector_set)
    self.letter_count = previous_collector_set[ItemLetterCountCollector].get_result()
    self.absolute_letter_frequencies = utilities.ProbabilityDistribution()


  def get_result(self, collector_set = None):
    return ((char, frequency / self.letter_count)
      for char, frequency in
        collector_set[ItemLetterAbsoluteFrequencyCollector].get_result(collector_set).iteritems())


  def as_str(self, collector_set = None):
    return str(dict(self.get_result(collector_set)))
