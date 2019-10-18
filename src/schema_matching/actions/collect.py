import sys, os.path, csv
from functools import partial as partialfn
from ..utilities.iterator import map_inplace
from ..utilities.functional import memberfn
from ..utilities.operator import noop
from ..collector.multiphase import MultiphaseCollector



def collect(src, collectorset_description, **kwargs):
	"""
	Collects info about the columns of the data set in file "path" according
	over multiple phases based on a description of those phases.

	:param src: io.IOBase | MultiphaseCollector
	:param collectorset_description: tuple[type | ItemCollector | callable]
	:return: MultiphaseCollector
	"""
	verbosity = kwargs.get('verbose', 0)

	if isinstance(src, MultiphaseCollector):
		multiphasecollector = src.reset()
	else:
		if verbosity >= 2:
			src_name = getattr(src, 'name', None)
			if src_name:
				print(src_name, end=':\n', file=sys.stderr)
		multiphasecollector = read_schema_instance(src, **kwargs)

	multiphasecollector.do_phases(collectorset_description,
		memberfn(print_phase_results, kwargs.get('number_format', '')) if verbosity >= 2 else None)
	if verbosity >= 2:
		print(file=sys.stderr)

	return multiphasecollector


def read_schema_instance(src, field_delimiter=',', verbosity=0, **kwargs):
	src_name = getattr(src, 'name', None)
	src_name = '<unknown schema instance>' if src_name is None else os.path.basename(src_name)
	reader = map(partialfn(map_inplace, str.strip),
		csv.reader(src, delimiter=field_delimiter, skipinitialspace=True))
	result = MultiphaseCollector(reader, src_name, verbosity)
	getattr(src, 'close', noop)()
	return result


def print_phase_results(multiphasecollector, number_format=''):
	print(multiphasecollector.merged_predecessors.as_str(number_format), file=sys.stderr)
