from __future__ import division
from collector import ItemCollector
from collector.count import ItemCountCollector
from collector.lettercount import ItemLetterCountCollector

class ItemLetterAverageCollector(ItemCollector):

    def __init__(self, previous_collector_set = None):
      ItemCollector.__init__(self, previous_collector_set)


    result_dependencies = (ItemLetterCountCollector, ItemCountCollector)


    def get_result(self, collector_set):
        return collector_set[ItemLetterCountCollector].get_result() / collector_set[ItemCountCollector].get_result()
