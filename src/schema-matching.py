#!/usr/bin/python3 -OO
import sys, os.path, signal
import itertools, operator, collections, math
import io, csv
from itertools import repeat
from functools import partial as partialfn
from actions import argument_parser

import utilities.iterator, utilities.operator, utilities.argparse
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
  opts = argument_parser.parse_args(argv)


  if opts.action[0] == 'match':
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
      "Warning: The time limit option doesn't work with the '", opts.action[0],
      "' action.",
      sep='', file=sys.stderr)

  dispatcher = (
      __single_collectorset_description_action
    if opts.action[1] == 1 else
      __multi_collectorset_description_action)
  rv = dispatcher(opts)

  if (__interrupted):
    print(
      'The time limit of', opts.time_limit, 'seconds was reached. '
      'The results may be incomplete or inaccurate.',
      file=sys.stderr)
    if __debug__:
      print('INFO:', __timer() - __interrupted,
        'seconds between interruption and program termination.',
        file=sys.stderr)
  assert __interrupted is not None or not opts.time_limit or opts.action[0] != 'match'
  __interrupted = None

  return rv


def __single_collectorset_description_action(options):
  options = vars(options).copy()
  action = options.pop('action')
  assert action[1] == 1

  collectorset_descriptions = options.pop('collectorset_descriptions')
  if not collectorset_descriptions:
    from collector.description import default as default_description
    options['collectorset_description'] = default_description
  elif len(collectorset_descriptions) == 1:
    options['collectorset_description'] = collectorset_descriptions[0]
  else:
    argument_parser.error(
      "Action '{1}' only allows up to {2} collector set description; "
      "you supplied {0}.".format(
        len(collectorset_descriptions), *action))

  return globals()[action[0]](**options)


def __multi_collectorset_description_action(options):
  options = vars(options).copy()
  action = options.pop('action')

  collectorset_descriptions = options['collectorset_descriptions']
  if not collectorset_descriptions:
    argument_parser.error(
      "Action '{1}' requires at least one collector set description.".format(
        action[0]))
  elif len(collectorset_descriptions) == 1:
    from collector.description import default as default_description
    collectorset_descriptions.insert(0, default_description)

  return globals()[action[0]](**options)


def match(schema_instances, collectorset_description, **kwargs):
  assert len(schema_instances) == 2 # TODO: raise proper error

  collectors, sort_order, best_match = \
    collect_analyse_match(schema_instances, collectorset_description, **kwargs)
  assert len(best_match) == 1
  _, _, best_match_norm, best_match = best_match[0]
  isreversed = not utilities.iterator.issorted(sort_order)

  if kwargs.get('verbose', 0) >= 1:
    print('norm:', format(best_match_norm, kwargs.get('number_format', '')),
      file=sys.stderr)
  print_result(best_match, isreversed, **kwargs)
  return 0


def validate(schema_instances, collectorset_description, **kwargs):
  _, _, best_matches, stats = \
    validate_stats(schema_instances, collectorset_description, **kwargs)

  if len(best_matches) > 1:
    possible_count = stats[0] + stats[1]
    avg_norm = \
      math.fsum(map(operator.itemgetter(2), best_matches)) / len(best_matches)
    print("Total:",
      "{3} invalid, {4} impossible, and {5} missing matches, "
      "mean norm = {0:{1}}".format(
        avg_norm, kwargs.get('number_format', ''), *stats),
      "{} successful out of {} possible matches ({:.1%})".format(
        stats[0], possible_count, stats[0] / possible_count),
      sep='\n', file=kwargs.get('output', sys.stdout))

  return int(bool(stats[1] or stats[3]))


def validate_stats(schema_instances, collectorset_description, **kwargs):
  collectors, sort_order, best_matches = \
    collect_analyse_match(schema_instances, collectorset_description, **kwargs)
  if sort_order:
    schema_instances = \
      tuple(utilities.iterator.sort_by_order(schema_instances, sort_order))
  print_total = len(best_matches) > 1
  counts = (
    validate_result(
      (schema_instances[c1_idx].name, schema_instances[c2_idx].name),
      best_match, best_match_norm, print_total, **kwargs)
    for c1_idx, c2_idx, best_match_norm, best_match in best_matches)
  return (collectors, sort_order, best_matches, tuple(map(sum, zip(*counts))))


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
    assert utilities.iterator.issorted(collectors, __get_column_count)
    sort_order = None
    each(collect_functor, collectors)
  else:
    # The first collector shall have the least columns.
    sort_order, collectors = \
      utilities.iterator.sorted_with_order(
        map(collect_functor, collectors), __get_column_count)

  # analyse collected data
  norms_combinations = [
    [c1_idx, c2_idx,
      MultiphaseCollector.results_norms(collectors[c1_idx], collectors[c2_idx],
        collectorset_description.weights), None]
    for c1_idx, c2_idx in itertools.combinations(range(len(collectors)), 2)]

  if kwargs.get('verbose', 0) >= 1:
    formatter = memberfn(format, kwargs.get('number_format', ''))
    for c1_idx, c2_idx, norms, _ in norms_combinations:
      print(collectors[c2_idx].name, collectors[c1_idx].name,
        sep=' / ', end='\n| ', file=sys.stderr)
      print(*('  '.join(map(formatter, row)) for row in norms),
        sep=' |\n| ', end=' |\n\n', file=sys.stderr)

  # find minimal combinations
  for norms_combination in norms_combinations: # TODO: rewrite as functional clause
    norms_combination[2:4] = get_best_schema_mapping(norms_combination[2])

  return collectors, sort_order, norms_combinations


def __get_column_count(collector):
  return len(collector.merged_predecessors)


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
    if verbosity >= 2 and isinstance(src, io.IOBase):
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
  src_name = getattr(src, 'name', None) if isinstance(src, io.IOBase) else None
  src_name = '<unknown schema instance>' if src_name is None else os.path.basename(src_name)
  reader = map(partialfn(map_inplace, str.strip),
    csv.reader(src, delimiter=field_delimiter,
      skipinitialspace=True))
  return MultiphaseCollector(reader, src_name, verbosity)


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


def validate_result(schema_instance_paths, found_mappings, norm, print_names=False, **kwargs):
  """
  :param schema_instance_paths: list[str | io.IOBase]
  :param found_mappings: list[int]
  :return: (int, int, int, int)
  """
  assert len(schema_instance_paths) == 2
  out = kwargs.get('output', sys.stdout)
  schema_desc = tuple(map(read_schema_descriptor, schema_instance_paths))
  rschema_desc = tuple(map(utilities.rdict, schema_desc))

  if print_names:
    print(*map(os.path.basename, schema_instance_paths), sep=' => ', file=out)

  # build column mapping dictionary
  offset = kwargs.get('column_offset', 1)
  found_mappings = {k + offset: v + offset
    for k, v in enumerate(found_mappings) if v is not None}
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

  successful_count = len(found_mappings) - invalid_count - impossible_count
  print(
    '{} successful, {} invalid, {} impossible, and {} missing matches, '
    'norm = {:{}}'.format(
      successful_count, invalid_count, impossible_count, missing_count, norm,
      kwargs.get('number_format', '')),
    end='\n\n', file=out)

  return successful_count, invalid_count, impossible_count, missing_count


def read_schema_descriptor(schema_src):
  """
  :param schema_src: str | io.IOBase
  :return: dict[int, int]
  """
  with open(os.path.splitext(schema_src)[0] + '_desc.txt') as f:
    return {
      int(mapped): int(original)
      for mapped, original in map(memberfn(str.split, ',', 1), f)
    }


def compare_descriptions(schema_instances, collectorset_descriptions, **kwargs):
  assert len(collectorset_descriptions) >= 2
  out = kwargs.get('output', sys.stdout)

  collectors = sorted(
    map(memberfn(read_schema_instance, **kwargs), schema_instances),
    key=__get_column_count)
  overall_stats = []

  for desc in collectorset_descriptions:
    _, _, best_matches, stats = validate_stats(
      tuple(map(MultiphaseCollector.copy, collectors)), desc, **kwargs)
    avg_norm = \
      math.fsum(map(operator.itemgetter(2), best_matches)) / len(best_matches)
    overall_stats.append((desc, stats[1] + stats[2], avg_norm))
    print_description_comment(desc, out)

  overall_stats.sort(key=operator.itemgetter(slice(1, 3)))
  number_format = kwargs.get('number_format', '')
  rank_format = str(max(math.ceil(math.log10(len(overall_stats) + 1)), 1)) + 'd'

  i = 1
  last_error_count = None
  for stats in overall_stats:
    print(
      "{0:{1}}. {3.__file__} ({3.__name__}), errors={4}, "
      "mean norm={5:{2}}".format(
        i, rank_format, number_format, *stats),
      file=out)
    if last_error_count != stats[1]:
      last_error_count = stats[1]
      i += 1

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
  print(
    "... with collector descriptions and weights from {0.__file__} "
    "({0.__name__}).".format(
      desc),
    end='\n\n', file=out)


def __timeout_handler(signum, frame):
  if signum == signal.SIGALRM:
    global __interrupted
    __interrupted = __timer() if __debug__ else True


if __name__ == '__main__':
  sys.exit(main())
