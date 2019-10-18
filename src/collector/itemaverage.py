from .base import ItemCollector
from .itemsum import ItemSumCollector
from .itemcount import ItemCountCollector



class ItemAverageCollector(ItemCollector):

	result_dependencies = (ItemCountCollector, ItemSumCollector)


	def get_result(self, collector_set):
		sumcoll = collector_set[ItemSumCollector]
		return (sumcoll.get_result() /
			(collector_set[ItemCountCollector].get_result() - sumcoll.type_error_count))
