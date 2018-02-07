import numbers
from .base import ItemCollector
from .set import ItemCollectorSet



class ItemCountCollector(ItemCollector):

	def __init__(self, previous_collector_set = None):
		super().__init__(previous_collector_set)
		if isinstance(previous_collector_set, numbers.Integral):
			self.count = previous_collector_set
			self.set_collected()
		else:
			self.count = 0
			assert previous_collector_set is None or \
				isinstance(previous_collector_set, ItemCollectorSet)


	def collect(self, item, collector_set = None):
		assert not self.has_collected
		self.count += 1


	def get_result(self, collector_set = None):
		assert self.has_collected
		return self.count
