import collections
from collector import ItemCollector
from collector.lettercount import ItemLetterCountCollector
from collector.absoluteletterfrequency import ItemLetterAbsoluteFrequencyCollector


class ItemLetterRelativeFrequencyCollector(ItemCollector):
  def __init__(self, previous_collector_set):
    ItemCollector.__init__(self, previous_collector_set)
    self.letter_count = previous_collector_set[ItemLetterCountCollector].get_result()
    self.absolute_letter_frequencies = collections.defaultdict(int)

  def get_result(self, collector_set):
    return {(k, v / self.letter_count)
            for k, v in collector_set[ItemLetterAbsoluteFrequencyCollector].items()}
