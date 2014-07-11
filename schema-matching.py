#!/usr/bin/python -OO
from __future__ import print_function, absolute_import
import sys, os.path
import itertools, functools, operator, collections
import csv, imp
import utilities, utilities.file
from utilities import infinity
from utilities.string import DecodableUnicode
import utilities.iterator as uiterator
import utilities.functional as ufunctional
from collector import MultiphaseCollector
from collector.columntype import ColumnTypeItemCollector


number_format = '10.4e'

def main(*argv):
  """
  :param argv: tuple[str]
  :return: int
  """

  # parse arguments
  argv = collections.deque(argv)

  # action to perform
  action = None
  if argv[0].startswith('--'):
    action = argv.popleft()[2:]

  # input files
  in_paths = [argv.popleft()]
  in_paths.append(argv.popleft())

  # output file
  if argv:
    sys.stdout = utilities.file.openspecial(argv.popleft(), 'w')

  # determine collector descriptions to use
  collector_description = \
    get_collector_description(argv.popleft() if argv else None)

  # read and analyse data
  collectors, isreversed, best_match = \
    collect_analyse_match(in_paths, collector_description)

  # print or validate best match
  if action is None:
    print('norm:', format(best_match[0], number_format), file=sys.stderr)
    print_result(best_match[1], isreversed)
    return 0

  elif action == 'validate':
    validation_result = validate_result(in_paths, best_match[1])
    print('\n{2} invalid, {3} impossible, and {4} missing matches, norm = {0:{1}}'.format(
      best_match[0], number_format, *validation_result))
    return int(validation_result[0] or validation_result[2])

  else:
    print('Unknown action:', action, file=sys.stderr)
    return 2




def get_collector_description(srcpath=None):
  """
  :param srcpath: str
  :return: dict
  """
  if srcpath:
    import collector.description as parent_package
    collector_description = imp.load_source(
      utilities.get_unique_name('collector.description._anonymous_{:08x}',
        sys.modules),
      srcpath)
  else:
    import collector.description.default as collector_description
  return {k: getattr(collector_description, k, None)
    for k in ('phase_description', 'collector_weights')}


def collect_analyse_match(collectors, collector_description):
  """
  :param collectors: list[basestring | MultiphaseCollector]
  :param collector_description: dict
  :return: list[MultiphaseCollector], bool, tuple[int]
  """
  assert isinstance(collectors, collections.Sequence) and len(collectors) == 2
  collect_functor = \
    ufunctional.apply_memberfn(collect,
      *collector_description['phase_description'])

  if isinstance(collectors[0], MultiphaseCollector):
    assert isinstance(collectors[1], MultiphaseCollector)
    uiterator.each(collect_functor, collectors)
  else:
    collectors = map(collect_functor, collectors)

  # The first collector shall have the least columns.
  isreversed = len(collectors[0].merged_predecessors) > len(collectors[1].merged_predecessors)
  if isreversed:
    collectors.reverse()

  # analyse collected data
  norms = MultiphaseCollector.results_norms(*collectors,
    weights=collector_description['collector_weights'])
  if __debug__:
    print(collectors[1].name, collectors[0].name, sep=' / ', end='\n| ', file=sys.stderr)
    formatter = ufunctional.apply_memberfn(format, number_format)
    print(
      *['  '.join(itertools.imap(formatter, row)) for row in norms],
      sep=' |\n| ', end=' |\n\n', file=sys.stderr)

  # find minimal combination
  return collectors, isreversed, get_best_schema_mapping(norms)


def collect(src, *phase_descriptions):
  """
  Collects info about the columns of the data set in file "path" according
  over multiple phases based on a description of those phases.

  :param path: str, MultiphaseCollector
  :param phase_descriptions: tuple[tuple[type | ItemCollector | callable]]
  :return: MultiphaseCollector
  """
  if isinstance(src, MultiphaseCollector):
    multiphasecollector = src

  else:
    if __debug__:
      print(src, end=':\n', file=sys.stderr)

    with open(src, 'rb') as f:
      reader = csv.reader(f, delimiter=';', skipinitialspace=True)
      reader = itertools.imap(
        functools.partial(uiterator.map_inplace,
          lambda item: DecodableUnicode(item.strip())),
        reader)
      multiphasecollector = MultiphaseCollector(reader, os.path.basename(src))

  phase_descriptions = (
    ((ColumnTypeItemCollector(len(multiphasecollector.rowset)),),) +
    phase_descriptions)
  for phase_description in phase_descriptions:
    multiphasecollector(*phase_description)
    if __debug__:
      print(multiphasecollector.merged_predecessors.as_str(number_format), file=sys.stderr)
  if __debug__:
    print(file=sys.stderr)

  return multiphasecollector


def get_best_schema_mapping(distance_matrix):
  """
  :param distance_matrix: list[list[float]]
  :return: (float, tuple[int])
  """
  # TODO: clean this function up and optimise it
  assert operator.eq(*utilities.minmax(map(len, distance_matrix)))
  successor = (1).__add__
  predecessor = (-1).__add__

  maxI = len(distance_matrix) # row count
  maxJ = len(distance_matrix[0]) # column count
  assert maxI >= maxJ
  rangeI = xrange(maxI)
  rangeJ = xrange(maxJ)
  known_mappings = list(itertools.repeat(None, maxJ))
  #ismapped = list(itertools.repeat(False, maxJ))
  def unmapped(): return itertools.ifilter(lambda j: known_mappings[j] is None, rangeJ)

  def sweep_row(i, skippable_count):
    if skippable_count < 0:
      return infinity, None
    if i == maxI:
      return 0, tuple(known_mappings)

    # try to skip column j
    minlength, minpath = sweep_row(i + 1, skippable_count - 1)

    for j in unmapped():
      d = distance_matrix[i][j]
      if d is not infinity:
        known_mappings[j] = i
        length, path = sweep_row(i + 1, skippable_count)
        known_mappings[j] = None
        length += d
        if length < minlength:
          assert path is not None
          minlength = length
          minpath = path
    return minlength, minpath

  best_match = sweep_row(0, maxI - maxJ)
  if best_match[1] is not None:
    return best_match
  else:
    return best_match[0], tuple(itertools.repeat(None, maxI))


def validate_result(in_paths, found_mappings, offset=1):
  """
  :param in_paths: list[str]
  :param found_mappings: list[int]
  :param offset: int
  :return: (int, int, int)
  """

  # read expected column mappings
  def read_descriptor(path):
    """
    :param path: str
    :return: dict[int, int]
    """
    with open(os.path.splitext(path)[0] + '_desc.txt') as f:
      return {
        int(mapped): int(original)
        for mapped, original
        in itertools.imap(ufunctional.apply_memberfn(str.split, ',', 1), f)
      }

  schema_desc = map(read_descriptor, in_paths)
  rschema_desc = map(utilities.rdict, schema_desc)

  # build column mapping dictionary
  found_mappings = {k + offset: v + offset for k, v in enumerate(found_mappings) if v is not None}
  invalid_count = 0
  impossible_count = 0

  # find mismatches
  for found_mapping in found_mappings.iteritems():
    original_mapping = map(dict.__getitem__, schema_desc, found_mapping)
    expected = rschema_desc[1].get(original_mapping[0])
    if expected is None:
      impossible_count += 1
    else:
      invalid_count += operator.ne(*original_mapping)

    print('found {2} => {3}, expected {2} => {0} -- {1}'.format(
      expected, 'ok' if found_mapping[1] == expected else 'MISMATCH!', *found_mapping))

  # find missing matches
  missing_count = 0
  for k in rschema_desc[0].viewkeys() | rschema_desc[1].viewkeys():
    v = rschema_desc[1].get(k)
    k = rschema_desc[0].get(k)
    if k is not None and v is not None and k not in found_mappings:
      print('expected {} => {} -- MISSED!'.format(k, v))
      missing_count += 1

  return invalid_count, impossible_count, missing_count


def print_result(column_mappings, reversed=False, offset=1):
  """
  :param column_mappings: list[int]
  :param reversed: bool
  :param offset: int
  """
  column_mappings = [
    itertools.imap(str, xrange(offset, offset.__add__(len(column_mappings)))),
    itertools.imap(ufunctional.composefn(offset.__add__, str), column_mappings)
  ]
  if reversed:
    column_mappings.reverse()
  print(*itertools.imap(','.join, itertools.izip(*column_mappings)), sep='\n')


if __name__ == '__main__':
  assert DecodableUnicode.default_encoding.upper() == 'UTF-8'
  sys.stderr = utilities.file.fix_file_encoding(sys.stderr)
  sys.exit(main(*sys.argv[1:]))
