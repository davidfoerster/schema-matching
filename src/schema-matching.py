#!/usr/bin/python3 -OO
import sys, os.path, signal
import operator, collections, argparse
import csv
from itertools import repeat
from functools import partial as partialfn

import utilities.operator, utilities.argparse
from utilities import infinity
from utilities.iterator import each, map_inplace
from utilities.functional import memberfn, composefn
import collector.description
from collector.multiphase import MultiphaseCollector

if __debug__:
  from timeit import default_timer as __timer


__interrupted = None


def main(argv=None):
  global __interrupted

  opts = __argument_parser.parse_args(argv)

  if opts.action == 'match':
    # default action; set up alarm handler
    if __interrupted is not None:
      raise RuntimeError("Schema matching is not re-entrant, if a time limit is used")
    __interrupted = False
    if opts.time_limit > 0:
      signal.signal(signal.SIGALRM, __timeout_handler)
      if signal.alarm(opts.time_limit):
        raise RuntimeError('Who set the alarm before us?!!')
  elif opts.time_limit:
    print(
      "Warning: The time limit option doesn't work with the '", opts.action,
      "' action.",
      sep='', file=sys.stderr)

  rv = schema_matching(**vars(opts))

  if (__interrupted):
    print(
      'The time limit of', opts.time_limit, 'seconds was reached. '
      'The results may be incomplete or inaccurate.',
      file=sys.stderr)
    if __debug__:
      print('INFO:', __timer() - __interrupted,
        'seconds between interruption and program termination.',
        file=sys.stderr)
  assert __interrupted is not None or not opts.time_limit or opts.action != 'match'
  __interrupted = None

  return rv


def __get_argument_parser():
  p = argparse.ArgumentParser(description='Match data schema attributes.')

  action_group = p.add_mutually_exclusive_group(required=True)
  def add_action(name, shortopt='-'):
    flags = ['--' + name]
    if shortopt is not None:
      if shortopt == '-':
        shortopt = name[0].upper()
      assert len(shortopt) == 1 and shortopt.isalpha()
      flags.insert(0, '-' + shortopt)
    return action_group.add_argument(*flags, dest='action',
      action='store_const', const=name)

  add_action('match')
  add_action('validate')
  add_action('compare-descriptions')

  p.add_argument('schema_instances', nargs=range(2, sys.maxsize),
    type=argparse.FileType('r'), action=utilities.argparse.NargsRangeAction,
    metavar='schema-instances')

  p.add_argument('-d', '--desc', action='append', dest='collector_descriptions',
    type=collector.description.argparser, metavar='collector-descriptions')

  p.add_argument('-o', '--output', type=argparse.FileType('w'),
    default=sys.stdout)

  p.add_argument('--time-limit', type=int, choices=range(sys.maxsize),
    default=0, metavar='seconds')

  p.add_argument('--field-delimiter', default=';')
  p.add_argument('--number-format', default='.3e')
  p.add_argument('-v', '--verbose', action='count', default=int(__debug__))

  return p

__argument_parser = __get_argument_parser()


def schema_matching(action, schema_instances, collector_descriptions=None, **kwargs):
  if len(schema_instances) < 2:
    raise IndexError("At least 2 schema instances are required")
  if len(schema_instances) > 2:
    raise NotImplementedError("More than 2 schema instances aren't implemented yet")
  if not isinstance(schema_instances, list):
    list(schema_instances)

  if collector_descriptions is None:
    collector_descriptions = ()
  elif collector_descriptions:
    collector_descriptions = list(collector_descriptions)

  # determine collector descriptions to use
  if collector_descriptions:
    collector_description = collector_descriptions.pop()
  else:
    from collector.description import default as collector_description

  # read and analyse data
  collectors, isreversed, best_match = \
    collect_analyse_match(schema_instances, collector_description, **kwargs)
  best_match_norm, best_match = best_match

  if isreversed:
    schema_instances.reverse()
  each(operator.methodcaller('close'), schema_instances)
  map_inplace(operator.attrgetter('name'), schema_instances)

  # print or validate best match
  if action == 'match':
    if kwargs.get('verbose', 0) >= 1:
      print('norm:', format(best_match_norm, kwargs.get('number_format', '')),
        file=sys.stderr)
    print_result(best_match, isreversed, **kwargs)

  elif action == 'validate':
    invalid_count, impossible_count, missing_count = \
      validate_result(schema_instances, best_match, best_match_norm, **kwargs)
    return int(bool(invalid_count | missing_count))

  elif action == 'compare-descriptions':
    return compare_descriptions(schema_instances, collectors, collector_descriptions,
      (collector_description, best_match_norm, best_match), **kwargs)

  else:
    print('Unknown action:', action, file=sys.stderr)
    return 2

  return 0


def collect_analyse_match(collectors, collector_descriptions, **kwargs):
  """
  :param collectors: list[str | MultiphaseCollector]
  :param collector_descriptions: object
  :return: list[MultiphaseCollector], bool, tuple[int]
  """
  assert isinstance(collectors, collections.Sequence) and len(collectors) == 2
  collect_functor = \
    memberfn(collect, collector_descriptions.descriptions, **kwargs)

  if isinstance(collectors[0], MultiphaseCollector):
    assert isinstance(collectors[1], MultiphaseCollector)
    each(collect_functor, collectors)
  else:
    collectors = list(map(collect_functor, collectors))

  # The first collector shall have the least columns.
  isreversed = len(collectors[0].merged_predecessors) > len(collectors[1].merged_predecessors)
  if isreversed:
    collectors.reverse()

  # analyse collected data
  norms = MultiphaseCollector.results_norms(*collectors,
    weights=collector_descriptions.weights)
  if kwargs.get('verbose', 0) >= 1:
    print(collectors[1].name, collectors[0].name, sep=' / ', end='\n| ', file=sys.stderr)
    formatter = memberfn(format, kwargs.get('number_format', ''))
    print(*('  '.join(map(formatter, row)) for row in norms),
      sep=' |\n| ', end=' |\n\n', file=sys.stderr)

  # find minimal combination
  return collectors, isreversed, get_best_schema_mapping(norms)


def collect(src, collector_descriptions, **kwargs):
  """
  Collects info about the columns of the data set in file "path" according
  over multiple phases based on a description of those phases.

  :param src: str, MultiphaseCollector
  :param collector_descriptions: tuple[type | ItemCollector | callable]
  :return: MultiphaseCollector
  """
  verbosity = kwargs.get('verbose', 0)

  if isinstance(src, MultiphaseCollector):
    multiphasecollector = src.reset()

  else:
    if verbosity >= 2:
      print(src.name, end=':\n', file=sys.stderr)

    reader = map(partialfn(map_inplace, str.strip),
      csv.reader(src, delimiter=kwargs.get('field_delimiter', ','),
        skipinitialspace=True))
    multiphasecollector = \
      MultiphaseCollector(reader, os.path.basename(src.name), verbosity)

  multiphasecollector.do_phases(collector_descriptions,
    memberfn(print_phase_results, kwargs.get('number_format', '')) if verbosity >= 2 else None)
  if verbosity >= 2:
    print(file=sys.stderr)

  return multiphasecollector


def print_phase_results(multiphasecollector, number_format=''):
  print(multiphasecollector.merged_predecessors.as_str(number_format), file=sys.stderr)


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

  def iter_unmapped():
    return filter(lambda j: known_mappings[j] is None, rangeJ)

  def sweep_row(i, skippable_count):
    if __interrupted or skippable_count < 0:
      return infinity, None
    if i == maxI:
      return 0, tuple(known_mappings)

    # try to skip column j
    minlength, minpath = sweep_row(successor(i), predecessor(skippable_count))

    for j in iter_unmapped():
      if __interrupted:
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


def validate_result(in_paths, found_mappings, norm, **kwargs):
  """
  :param in_paths: list[str]
  :param found_mappings: list[int]
  :param offset: int
  :return: (int, int, int)
  """
  out = kwargs.get('output', sys.stdout)

  # read expected column mappings
  def read_descriptor(path):
    """
    :param path: str
    :return: dict[int, int]
    """
    with open(os.path.splitext(path)[0] + '_desc.txt') as f:
      return {
        int(mapped): int(original)
        for mapped, original in map(memberfn(str.split, ',', 1), f)
      }

  schema_desc = tuple(map(read_descriptor, in_paths))
  rschema_desc = tuple(map(utilities.rdict, schema_desc))

  # build column mapping dictionary
  offset = kwargs.get('column_offset', 1)
  found_mappings = {k + offset: v + offset for k, v in enumerate(found_mappings) if v is not None}
  invalid_count = 0
  impossible_count = 0

  # find mismatches
  for found_mapping in found_mappings.items():
    original_mapping = tuple(map(dict.__getitem__, schema_desc, found_mapping))
    expected = rschema_desc[1].get(original_mapping[0])
    if expected is None:
      impossible_count += 1
    else:
      invalid_count += operator.ne(*original_mapping)

    print('found {2} => {3}, expected {2} => {0} -- {1}'.format(
      expected, 'ok' if found_mapping[1] == expected else 'MISMATCH!', *found_mapping),
      file=out)

  # find missing matches
  missing_count = 0
  for k in rschema_desc[0].keys() | rschema_desc[1].keys():
    v = rschema_desc[1].get(k)
    k = rschema_desc[0].get(k)
    if k is not None and v is not None and k not in found_mappings:
      print('expected {} => {} -- MISSED!'.format(k, v))
      missing_count += 1

  print('\n{} invalid, {} impossible, and {} missing matches, norm = {:{}}'.format(
    invalid_count, impossible_count, missing_count, norm, kwargs.get('number_format', '')),
    file=out)

  return invalid_count, impossible_count, missing_count


def compare_descriptions(in_paths, collectors, to_compare, desc=None, **kwargs):
  """
  :param collectors: list[str | MultiphaseCollector]
  :param to_compare: tuple[object]
  :param desc: dict, float, tuple(int)
  :return:
  """
  from collector.description import default as default_description
  out = kwargs.get('output', sys.stdout)
  descriptions = []

  if desc:
    desc, best_match_norm, best_match = desc
    if not to_compare and (desc is default_description or
      os.path.samefile(desc.__file__, default_description.__file__)
    ):
      print("Warning: I won't compare the default description to itself.", file=sys.stderr)

    invalid_count, _, missing_count = \
      validate_result(in_paths, best_match, best_match_norm, **kwargs)
    print_description_comment(desc, out)
    descriptions.append((desc, invalid_count + missing_count, best_match_norm))

  if not to_compare:
    to_compare = (default_description,)

  for desc in to_compare:
    collectors, _, best_match = collect_analyse_match(collectors, desc, **kwargs)
    best_match_norm, best_match = best_match
    invalid_count, _, missing_count = \
      validate_result(in_paths, best_match, best_match_norm, **kwargs)
    print_description_comment(desc, out)
    descriptions.append((desc, invalid_count + missing_count, best_match_norm))

  i = 1
  last_error_count = None
  number_format = kwargs.get('number_format', '')
  descriptions.sort(key=operator.itemgetter(slice(1, 3)))
  for desc in descriptions:
    print('{}. {}, errors={}, norm={:{}}'.format(
      i, desc[0].__file__, desc[1], desc[2], number_format),
      file=out)
    i += last_error_count != desc[1]
    last_error_count = desc[1]

  return 0



def print_result(column_mappings, reversed=False, **kwargs):
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
  print(*map(','.join, zip(*column_mappings)),
    sep='\n', file=kwargs.get('output', sys.stdout))


def print_description_comment(desc, out):
  print('... with collector descriptions and weights from {} ({}).'.format(
    desc.__file__, desc.__name__),
    end='\n\n', file=out)


def __timeout_handler(signum, frame):
  if signum == signal.SIGALRM:
    global __interrupted
    __interrupted = __timer() if __debug__ else True


if __name__ == '__main__':
  sys.exit(main())
