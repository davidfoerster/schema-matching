# coding=utf-8

import re, itertools
from numbers import Number
from .. import utilities
from ..utilities import functional, string, infinity
from ..utilities.iterator import countif
from .base import ItemCollector
from .itemcount import ItemCountCollector


__decimal_regex = re.compile(r"\s*([-+]?)(|\d[^,.]*?|[^,.]*\d|.*?([,.]).*?)\s*$")

def decimal_info(item):
	m = re.match(__decimal_regex, item)
	if not m:
		return None

	start, end = m.span(2)
	if start != len(item) and not (item[start].isdigit() or item[end-1].isdigit()):
		return None

	if start == end:
		sign = m.group(1)
		return ('', len(sign), 0) if not sign or sign == '-' else None

	if start == m.start(3) and end == m.end(3):
		return None

	total_len = end - start
	potential_digits = itertools.islice(item, start, end)
	decimal_separator = m.group(3) if m.start(3) >= 0 else ''
	invalid_char_count = total_len - len(decimal_separator) - \
		 countif(type(item).isdigit, potential_digits)
	total_len += m.end(1) - m.start(1)
	return decimal_separator, total_len, invalid_char_count


def tofloat(item):
	item = item.replace(',', '.', 1)
	try:
		return float(item)
	except ValueError:
		return None


def toint(item):
	try:
		return int(item)
	except ValueError:
		return None



def _make_type_distance_matrix(type_sequence):
	return [
		[
				float(a is not b)
			if isinstance(a, Number) is isinstance(b, Number) else
				infinity
			for a in type_sequence
		]
		for b in type_sequence
	]

class ColumnTypeItemCollector(ItemCollector):

	result_dependencies = (ItemCountCollector,)

	__type_sequence = (int, float, str)
	__type_rdict = utilities.rdict(enumerate(__type_sequence))
	__distance_matrix = _make_type_distance_matrix(__type_sequence)
	__transformers = (toint, tofloat, str)


	@staticmethod
	def __get_set_length(x):
		if isinstance(x, dict):
			icc = x.get(ItemCountCollector)
			if icc:
				return icc.get_result(x)
		return None


	def __init__(self, collector_set=None, max_invalid_absolute=2, max_invalid_relative=0.25, total_max_invalid=0.05):
		super().__init__()
		self.__type_index = -1
		self.__tolerance_exceeded_count = 0

		self.max_invalid_absolute = max_invalid_absolute
		self.max_invalid_relative = max_invalid_relative
		self.total_max_invalid = total_max_invalid
		set_length = self.__get_set_length(collector_set)
		self.__total_max_invalid_absolute = (
			set_length and int(set_length * self.total_max_invalid))


	def collect(self, item, collector_set = None):
		assert not self.has_collected
		if self.__type_index <= 0: # none or int
			if item == '-' or item.isdigit():
				self.__type_index = 0
				return
			self.__type_index = 1

		if self.__type_index == 1: # float
			info = decimal_info(item)
			if info:
				if not info[2]:
					return
				if (info[2] <= self.max_invalid_absolute and
					info[2] <= info[1] * self.max_invalid_relative
				):
					self.__tolerance_exceeded_count += 1
					if not self.__total_max_invalid_absolute < self.__tolerance_exceeded_count:
						return
			self.__type_index += 1


	def get_result(self, collector_set = None):
		assert self.has_collected
		if self.__type_index == 1 and self.__total_max_invalid_absolute is None:
			set_length = self.__get_set_length(collector_set)
			self.__total_max_invalid_absolute = \
				0 if set_length is None else int(set_length * self.total_max_invalid)
			if self.__total_max_invalid_absolute < self.__tolerance_exceeded_count:
				self.__type_index += 1

		return self.__type_sequence[self.__type_index]


	def get_transformer(self):
		return self.__transformers[self.__type_index]


	@staticmethod
	def result_norm(a, b):
		return (
			ColumnTypeItemCollector.__distance_matrix
				[ColumnTypeItemCollector.__type_rdict[a]]
				[ColumnTypeItemCollector.__type_rdict[b]])


	def as_str(self, collector_set = None, format_spec=None):
		return utilities.string.join('(', self.get_result(None).__name__, ':',
			str(self.__tolerance_exceeded_count), ')')


	def __format__(self, format_spec=None): return self.as_str()

	def __str__(self): return self.as_str()



class factory(object):

	__pre_dependencies = (ColumnTypeItemCollector,)


	def __init__(self, string_collector, numeric_collector):
		super().__init__()
		self.string_collector = string_collector
		self.numeric_collector = numeric_collector
		self.pre_dependencies = frozenset(itertools.chain(self.__pre_dependencies,
			*_imap_attr('pre_dependencies', (), string_collector,
				numeric_collector)))
		self.result_dependencies = frozenset(itertools.chain(
			*_imap_attr('result_dependencies', (), string_collector,
				numeric_collector)))


	def __call__(self, type_or_predecessor):
		if isinstance(type_or_predecessor, dict):
			predecessor = type_or_predecessor
			type = predecessor[ColumnTypeItemCollector].get_result()
		else:
			predecessor = None
			type = type_or_predecessor
		return ItemCollector.get_instance(self.__for_type(type), predecessor)


	def get_type(self, collector_set):
		if collector_set:
			ctc = collector_set.get(ColumnTypeItemCollector)
			if ctc is not None:
				return self.__for_type(ctc.get_result())
		return self


	def __for_type(self, type):
		return self.numeric_collector if issubclass(type, Number) else self.string_collector


	def __eq__(self, other):
		return (isinstance(other, factory) and
			self.string_collector == other.string_collector and
			self.numeric_collector == other.numeric_collector)


	def __ne__(self, other):
		return not self.__eq__(other)


	def __hash__(self):
		return 0x4a9fd98f ^ hash(self.string_collector) ^ hash(self.numeric_collector)



def _imap_attr(attr, default, *objects):
	return map(utilities.functional.memberfn(getattr, attr, default), objects)
