from .base import ItemCollector
from .itemcount import ItemCountCollector
from .lettercount import ItemLetterCountCollector



class ItemLetterAverageCollector(ItemCollector):

		result_dependencies = (ItemLetterCountCollector, ItemCountCollector)


		def get_result(self, collector_set):
				return (
					collector_set[ItemLetterCountCollector].get_result()
						/ collector_set[ItemCountCollector].get_result())
