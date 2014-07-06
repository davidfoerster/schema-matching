from collector import ItemCollector
from collector.count import ItemCountCollector
from collector.lettercount import ItemLetterCountCollector

class ItemLetterAverageCollector(ItemCollector):

    def dependencies(self):
        """Return collector types this collector depends on"""
        return ItemLetterCountCollector, ItemCountCollector

    def get_result(self, collector_set):
        return collector_set[ItemLetterCountCollector].get_result() / collector_set[ItemCountCollector].get_result()
