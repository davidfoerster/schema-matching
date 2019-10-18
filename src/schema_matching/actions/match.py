import sys
import collections, itertools, operator
from itertools import repeat
from functools import partial as partialfn
from .. import utilities
from ..utilities import iterator, infinity
from ..utilities.iterator import each, map_inplace
from ..utilities.functional import memberfn, composefn
from ..collector.multiphase import MultiphaseCollector
from ..utilities.timelimit import Timelimit
from .collect import collect



def match(schema_instances, collectorset_description, **kwargs):
	assert len(schema_instances) == 2 # TODO: raise proper error
	with Timelimit(kwargs.pop('time_limit', None)):
		collectors, sort_order, best_match = \
			collect_analyse_match(schema_instances, collectorset_description, **kwargs)
		assert len(best_match) == 1
		_, _, best_match_norm, best_match = best_match[0]
		isreversed = not utilities.iterator.issorted(sort_order)

		if kwargs.get('verbose', 0) >= 1:
			print('norm:', format(best_match_norm, kwargs.get('number_format', '')),
				file=sys.stderr)
		print_match_result(best_match, isreversed, **kwargs)
	return 0


def collect_analyse_match(collectors, collectorset_description, **kwargs):
	"""
	:param collectors: list[io.IOBase | MultiphaseCollector]
	:param collectorset_description: object
	:return: list[MultiphaseCollector], list[int], list[int, int, float, list[int]]
	"""
	assert isinstance(collectors, collections.Sequence) and len(collectors) >= 2
	collect_functor = \
		memberfn(collect, collectorset_description.descriptions, **kwargs)

	if isinstance(collectors[0], MultiphaseCollector):
		assert all(map(memberfn(isinstance, MultiphaseCollector), collectors))
		assert utilities.iterator.issorted(collectors, MultiphaseCollector.columncount)
		sort_order = None
		each(collect_functor, collectors)
	else:
		# The first collector shall have the least columns.
		sort_order, collectors = \
			utilities.iterator.sorted_with_order(
				map(collect_functor, collectors), MultiphaseCollector.columncount)

	# analyse collected data
	norms_combinations = [
		[c1_idx, c2_idx,
			MultiphaseCollector.results_norms(collectors[c1_idx], collectors[c2_idx],
				collectorset_description.weights), None]
		for c1_idx, c2_idx in itertools.combinations(range(len(collectors)), 2)]

	if kwargs.get('verbose', 0) >= 1:
		formatter = memberfn(format, kwargs.get('number_format', ''))
		for c1_idx, c2_idx, norms, _ in norms_combinations:
			print('Per-column norms:',
				collectors[c2_idx].name, '/', collectors[c1_idx].name,
				end='\n| ', file=sys.stderr)
			print(*('	 '.join(map(formatter, row)) for row in norms),
				sep=' |\n| ', end=' |\n\n', file=sys.stderr)

	# find minimal combinations
	for norms_combination in norms_combinations: # TODO: rewrite as functional clause
		norms_combination[2:4] = get_best_schema_mapping(norms_combination[2])

	return collectors, sort_order, norms_combinations


def get_best_schema_mapping(distance_matrix):
	"""
	:param distance_matrix: list[list[float]]
	:return: (float, tuple[int])
	"""
	assert operator.eq(*utilities.minmax(map(len, distance_matrix)))
	successor = (1).__add__
	predecessor = (1).__rsub__

	maxI = len(distance_matrix) # row count
	maxJ = len(distance_matrix[0]) # column count
	assert maxI >= maxJ
	rangeJ = range(maxJ)
	known_mappings = list(repeat(None, maxJ))

	iter_unmapped = partialfn(filter,
		composefn(known_mappings.__getitem__, partialfn(operator.is_, None)),
		rangeJ)

	def sweep_row(i, skippable_count):
		if Timelimit.interrupted_flag or skippable_count < 0:
			return infinity, None
		if i == maxI:
			return 0, tuple(known_mappings)

		# try to skip column j
		minlength, minpath = sweep_row(successor(i), predecessor(skippable_count))

		for j in iter_unmapped():
			if Timelimit.interrupted_flag:
				break
			d = distance_matrix[i][j]
			if d is not None:
				known_mappings[j] = i
				length, path = sweep_row(successor(i), skippable_count)
				known_mappings[j] = None
				length += d
				if length < minlength:
					assert path is not None
					minlength = length
					minpath = path
		return minlength, minpath

	return sweep_row(0, maxI - maxJ)


def print_match_result(column_mappings, reversed=False, **kwargs):
	"""
	:param column_mappings: list[int]
	:param reversed: bool
	:param offset: int
	"""
	if not column_mappings:
		return

	offset = kwargs.get('column_offset', 1)
	column_mappings = [
		map(str, range(offset, offset + len(column_mappings))),
		map(composefn(offset.__add__, str), column_mappings)
	]
	if reversed:
		column_mappings.reverse()
	print(*map(' <-> '.join, map(tuple, zip(*column_mappings))),
		sep='\n', file=kwargs.get('output', sys.stdout))
