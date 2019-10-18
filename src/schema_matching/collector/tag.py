from .base import ItemCollector
from ..utilities.string import join



class TagCollector(ItemCollector):

	def __init__(self, id, data=None, isdependency=False):
		super().__init__()
		self.set_collected()
		self.set_transformed()
		self.isdependency = isdependency
		self.__id = id
		self.data = data


	@property
	def id(self):
		return self.__id


	def as_str(self, collector_set, format_spec=None):
		return join(str(self.__id), ': ', str(self.data))


	def __eq__(self, other):
		return (self.__id == other or
			(isinstance(other, TagCollector) and self.__id == other.__id))


	def __ne__(self, other): return not self.__eq__(other)

	def __hash__(self): return hash(self.__id)

	def get_result(self, collector_set): return None

	def get_type(self, collector_set): return self
