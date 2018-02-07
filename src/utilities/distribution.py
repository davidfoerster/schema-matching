import numbers, array, itertools, operator, math
from collections import defaultdict
from math import fsum
from utilities import minmax2
from utilities.string import join, format_char



default_number_format = '.3g'



class DistributionTable(object):

	def count(self):
		return NotImplemented


	def __truediv__(self, divisor):
		return NotImplemented


	def __str__(self):
		return self.__format__(default_number_format)


	def normalize(self, count=None):
		if count is None:
			count = self.count()
		return self / count



class SparseDistributionTable(DistributionTable, defaultdict):
	""""Holds a probability distribution and can compute the distance to other dists"""

	def __init__(self, type=int, *args):
		"""
		:param type: type
		:param args: *
		:return:
		"""
		assert issubclass(type, numbers.Real)
		DistributionTable.__init__(self)
		defaultdict.__init__(self, type, *args)


	def distance_to(self, other):
		return fsum((abs(p - other[bin]) for bin, p in self.items())) + \
			fsum(p for bin, p in other.items() if bin not in self)


	def count(self):
		return sum(self.values())


	def increase(self, item, value=1):
		self[item] += value


	def __truediv__(self, divisor):
		"""
		:param divisor: numbers.Real
		:return: SparseDistributionTable
		"""
		divisor = float(divisor)
		return SparseDistributionTable(float,
			((k, v / divisor) for k, v in self.items()))


	def __format__(self, number_format_spec=''):
		return join('(',
			', '.join((
				'{}: {:{}}'.format(format_char(event), frequency, number_format_spec)
				for event, frequency in self.items())),
			')')



class UniformBinDistributionTable(DistributionTable):

	def __init__(self, start, stop, bincount=None, datatype=None, initializer=None):
		super().__init__()

		assert stop > start
		if bincount is None:
			bincount = int(math.ceil(stop - start))
		assert isinstance(bincount, numbers.Integral) and bincount >= 1
		self.lower = start
		self.upper = stop
		self.step = (stop - start) / bincount
		if self.__step.is_integer():
			self.__step = int(self.__step)

		if initializer is None:
			initializer = itertools.repeat(0, bincount)
		self.data = list(initializer) if datatype is None else array.array(datatype, initializer)
		excess = len(self.data) - bincount
		if excess > 0:
			del self.data[bincount:]
		elif excess < 0:
			self.data.extend(itertools.repeat(0, -excess))


	@property
	def step(self):
		return self.__step


	@step.setter
	def step(self, value):
		self.__step = value
		self.__invstep = 1. / value


	@property
	def invstep(self):
		return self.__invstep


	def datatype(self):
		return self.data.typecode if isinstance(self.data, array.array) else None


	def getbinlower(self, binidx):
		return binidx * self.__step + self.lower


	def getbinupper(self, binidx):
		return self.getbinlower(binidx + 1)


	def getbinlimits(self, binidx):
		return self.getbinlower(binidx), self.getbinupper(binidx)


	def getbinidx(self, key):
		if key <= self.lower:
			return 0
		if key >= self.upper:
			return len(self.data) - 1
		else:
			return self.__getbinidx_raw(key)


	def __getbinidx_raw(self, key):
		return int((key - self.lower) * self.__invstep)


	def __getitem__(self, key):
		return self.data[self.getbinidx(key)]


	def __setitem__(self, key, value):
		self.data[self.getbinidx(key)] = value


	def increase(self, key, value=1):
		self.data[self.getbinidx(key)] += value


	def __len__(self):
		return len(self.data)


	def __iter__(self):
		return iter(self.data)


	def count(self):
		return sum(self)


	def __truediv__(self, divisor):
		return UniformBinDistributionTable(self.lower, self.upper, len(self.data), 'd',
			map(float(divisor).__rtruediv__, self.data))


	def distance_to(self, other):
		"""
		:param other: UniformBinDistributionTable
		:return: float
		"""
		if isinstance(other, UniformBinDistributionTable):
			if self.lower == other.lower and self.upper == other.upper and self.__step == other.__step:
				other = other.data
			else:
				return self.__distance_to2(other)

		assert not hasattr(other, '__len__') or len(self.data) == len(other)
		return fsum(map(abs, map(operator.sub, self.data, other)))


	def __distance_to2(self, other):
		return (
			UniformBinDistributionTable.__distance_to2_lower(
				*minmax2(self, other, 'lower')) +
			UniformBinDistributionTable.__distance_to2_upper(
				*minmax2(self, other, 'upper', True)) +
			fsum(UniformBinDistributionTable.__distance_to2_middle_parts(
				*minmax2(self, other, 'step'))))


	def __distance_to2_middle_parts(self, other):
		assert self.__step <= other.__step
		assert self.lower < self.upper and other.lower < other.upper

		lower = max(self.lower, other.lower)
		self_binidx = self.__getbinidx_raw(lower)
		self_binlimits_next = self.getbinlimits(self_binidx)
		other_binidx = other.__getbinidx_raw(lower)
		other_binlimits = other.getbinlimits(other_binidx)

		while self_binidx < len(self.data) and other_binidx < len(other.data):
			self_binlimits = self_binlimits_next
			yield abs((self.data[self_binidx] * self.__invstep) - (other.data[other_binidx] * other.__invstep)) * \
				(min(self_binlimits[1], other_binlimits[1]) - max(self_binlimits[0], other_binlimits[0]))

			if self_binlimits[1] <= other_binlimits[1]:
				self_binidx	 += 1
				self_binlimits_next = self.getbinlimits(self_binidx)
			if self_binlimits[1] >= other_binlimits[1]:
				other_binidx += 1
				other_binlimits = other.getbinlimits(other_binidx)


	def __distance_to2_lower(self, other):
		"""
		:param other: UniformBinDistributionTable
		:return: float
		"""
		assert self.lower <= other.lower
		lower_bin_end = (
				self.__getbinidx_raw(other.lower)
			if self.upper > other.lower else
				len(self.data))
		lower = fsum(itertools.islice(self.data, 0, lower_bin_end))
		if lower_bin_end < len(self.data):
			lower += self.data[lower_bin_end] * self.__invstep * \
				(other.lower - self.getbinlower(lower_bin_end))
		return lower


	def __distance_to2_upper(self, other):
		"""
		:param other: UniformBinDistributionTable
		:return: float
		"""
		assert self.upper >= other.upper
		upper_bin_start = (
				self.__getbinidx_raw(other.upper)
			if self.lower < other.upper else
				0)
		upper = fsum(itertools.islice(self.data, upper_bin_start + 1, len(self.data)))
		if upper_bin_start < len(self.data):
			upper += self.data[upper_bin_start] * self.__invstep * \
				(self.getbinupper(upper_bin_start) - other.upper)
		return upper


	def __format__(self, number_format_spec=''):
		return join('[',
			', '.join((
				'[{2:{0}}-{3:{0}}): {1:{0}}'.format(
					number_format_spec, frequency, *self.getbinlimits(bin_idx))
				for bin_idx, frequency in enumerate(self))),
			']')


	@staticmethod
	def for_count(count, lower, upper, *args):
		""" uses Sturge's rule: ceil(1 + log2(count)) """
		return UniformBinDistributionTable(
			lower, upper, _sturges_rule(count), *args)


	@staticmethod
	def for_variance(count, lower, upper, variance, *args):
		""" uses Scott's rule, limited by the double of Sturge's """
		h = int(math.ceil(3.49 * math.sqrt(variance) / _cubicroot(count)))
		return UniformBinDistributionTable(
			lower, upper, min(h, 2 * _sturges_rule(count)), *args)


	@staticmethod
	def for_quartiles(count, lower, upper, q1, q3, *args):
		""" uses Freedman's and Diaconis' rule """
		h = int(math.ceil(2.0 * (q3 - q1) / _cubicroot(count)))
		return UniformBinDistributionTable(
			lower, upper, min(h, 2 * _sturges_rule(count)), *args)



def _sturges_rule(n):
	assert isinstance(n, numbers.Integral) and n > 0
	return (n - 1).bit_length() + 1


def _cubicroot(x):
	return x ** (1. / 3.)
