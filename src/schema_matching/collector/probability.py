from .base import ItemCollector



class BaseProbabilityCollector(ItemCollector):

	# result_dependencies = (*CountCollector, *FrequencyCollector)


	def __init__(self, previous_collector_set):
		super().__init__(previous_collector_set)
		self.__cached_result = None


	def get_result(self, collector_set):
		if self.__cached_result is None:
			self.__cached_result = \
				collector_set[self.result_dependencies[1]].get_result(collector_set) \
					.normalize(collector_set[self.result_dependencies[0]] \
						.get_result(collector_set))
		return self.__cached_result


	def as_str(self, collector_set, number_fmt=''):
		return format(self.get_result(collector_set), number_fmt)


	@staticmethod
	def result_norm(a, b):
		return a.distance_to(b)
