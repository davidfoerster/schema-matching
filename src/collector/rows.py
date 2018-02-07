import utilities.operator as uoperator
from operator import methodcaller
from utilities.iterator import each
from utilities.string import join



class RowCollector(list):
	"""Manages collectors for a set of rows"""

	def __init__(self, initialiser, verbosity=0):
		list.__init__(self, initialiser)

		self.__rowcount = 0
		if verbosity >= 2:
			import sys
			self.__stderr = sys.stderr
		else:
			self.__stderr = None


	def reset(self, collectors):
		self[:] = collectors
		self.__rowcount = 0


	def collect(self, items):
		"""Collects the data of all columns of a row"""
		if self.__stderr is not None and len(self) != len(items):
			self.__rowcount += 1
			print(
				'Row {} has {} columns, expected {}: {}'.format(
					self.__rowcount, len(items), len(self), items),
				file=self.__stderr)

		assert len(self) <= len(items)
		each(self.__collect_column, self, items)


	@staticmethod
	def __collect_column(collector, item):
		collector.collect(item, collector)


	def collect_all(self, rows):
		each(self.collect, rows)
		each(methodcaller('set_collected'), self)


	class __transformer(tuple):

		def __call__(self, items):
			for i, t in self:
				items[i] = t(items[i])


	def get_transformer(self):
		column_transformers = tuple(
			filter(uoperator.second,
				enumerate(map(methodcaller('get_transformer'), self))))

		if column_transformers:
			def row_transformer(items):
				for column_idx, column_transformer in column_transformers:
					items[column_idx] = column_transformer(items[column_idx])
		else:
			row_transformer = None

		return row_transformer


	def transform_all(self, rows):
		transformer = self.get_transformer()
		if transformer is not None:
			each(transformer, rows)
			each(methodcaller('set_transformed'), self)


	def results_norms(a, b, weights=None):
		get_result = methodcaller('get_result')
		# Materialise results of inner loop because they'll be scanned multiple times.
		resultsA = tuple(map(get_result, a))
		resultsB = map(get_result, b)
		return [
			[collB.result_norm(resultA, resultB, weights) for resultA in resultsA]
			for collB, resultB in zip(b, resultsB)
		]


	def as_str(self, format_spec=''):
		return join('(', ', '.join(map(methodcaller('as_str', None, format_spec), self)), ')')


	def __str__(self): return self.as_str()

	__format__ = as_str
