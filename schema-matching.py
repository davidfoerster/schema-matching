#!/usr/bin/python
from __future__ import print_function
import csv, sys, os.path, utilities, itertools, operator, math
import collector, collector.columntype
from collector import MultiphaseCollector
from collector.columntype import ColumnTypeItemCollector
from collector.itemaverage import ItemAverageCollector
from collector.letteraverage import ItemLetterAverageCollector
from collector.variance import ItemStandardDeviationCollector
from collector.lettervariance import LetterStandardDeviationCollector
from collector.relativeletterfrequency import ItemLetterRelativeFrequencyCollector


# TODO: tweak
collector_phase_description = (
  (collector.columntype.factory(
    ItemLetterAverageCollector, ItemAverageCollector),
  ),
  (collector.columntype.factory(
    LetterStandardDeviationCollector, ItemStandardDeviationCollector),
  collector.columntype.factory(
    ItemLetterRelativeFrequencyCollector, None)
  )
)

# TODO: tweak
collector_weights = {
  ItemAverageCollector: 1.5,
  ItemLetterAverageCollector: math.sqrt
}


def main(*argv):
  """
  :param argv: tuple[str]
  :return: int
  """
  in_paths = [argv[0], argv[1]]
  validate = False

  # determine mode and/or output file
  if len(argv) > 2:
    if argv[2] == '--validate':
      validate = True
    else:
      sys.stdout = utilities.openspecial(argv[2], 'w')


  # collect from both input files
  collectors = [collect(path, *collector_phase_description) for path in in_paths]

  # The first collector shall have the most columns.
  reversed = len(collectors[0].merged_predecessors) < len(collectors[1].merged_predecessors)
  if reversed:
    collectors.reverse()
    in_paths.reverse()

  # analyse collected data
  norms = MultiphaseCollector.results_norms(*collectors, weights=collector_weights)
  if __debug__:
    print(*norms, sep='\n', end='\n\n', file=sys.stderr)

  # find minimal combination
  best_match = get_best_schema_mapping(norms)
  if __debug__:
    print('norm:', best_match[0], file=sys.stderr)

  # print or validate best match
  if validate:
    validate = validate_result(in_paths, best_match[1], reversed)
    print('\n{} invalid, {} impossible, and {} missing matches'.format(*validate))
    return int(validate[0] or validate[2])

  else:
    print_result(best_match[1], reversed)
    return 0


def collect(path, *phase_descriptions):
  """
  Collects info about the columns of the data set in file "path" according
  over multiple phases based on a description of those phases.

  :param path: str
  :param phase_descriptions: tuple[tuple[type | ItemCollector | callable]]
  :return: MultiphaseCollector
  """
  if __debug__:
    print(path, end=':\n', file=sys.stderr)

  with open(path, 'r') as f:
    multiphasecollector = MultiphaseCollector(
      csv.reader(f, delimiter=';', skipinitialspace=True))
    utilities.map_inplace(str.strip, multiphasecollector.rowset, 1)

    multiphasecollector(ColumnTypeItemCollector(len(multiphasecollector.rowset)))
    if __debug__:
      print(multiphasecollector.merged_predecessors, file=sys.stderr)

    for phase_description in phase_descriptions:
      multiphasecollector(*phase_description)
      if __debug__:
        print(multiphasecollector.merged_predecessors, file=sys.stderr)
    if __debug__:
      print(file=sys.stderr)

    return multiphasecollector


def get_best_schema_mapping(distance_matrix):
  """
  :param distance_matrix: list[list[float]]
  :return: (float, tuple[int])
  """
  assert operator.eq(*utilities.minmax(map(len, distance_matrix)))
  infinity = float('inf')

  maxI = len(distance_matrix)
  rangeJ = xrange(len(distance_matrix[0]))
  known_mappings = list(itertools.repeat(None, maxI))
  ismapped = list(itertools.repeat(False, len(rangeJ)))

  def sweep_row(i):
    if i == maxI:
      return 0, tuple(known_mappings)

    minlength = infinity
    minpath = None
    for j in itertools.ifilterfalse(ismapped.__getitem__, rangeJ):
      d = distance_matrix[i][j]
      if d is None or minlength <= d:
        continue

      known_mappings[i] = j
      ismapped[j] = True
      length, path = sweep_row(i + 1)
      ismapped[j] = False
      if path is None:
        continue

      length += d
      if length < minlength:
        minlength = length
        minpath = path

    return minlength, minpath

  return sweep_row(0)


def validate_result(in_paths, column_mappings, reversed=False, offset=1):
  """
  :param in_paths: list[str]
  :param column_mappings: list[int]
  :param reversed: bool
  :param offset: int
  :return: (int, int, int)
  """

  # build column mapping dictionary
  column_mappings = {k + offset: v + offset for k, v in enumerate(column_mappings)}
  if reversed:
    mapping = utilities.rdict(column_mappings)

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
        in itertools.imap(utilities.apply_memberfn(str.split, ',', 2), f)
      }

  schema_desc = map(read_descriptor, in_paths)
  rschema_desc1 = utilities.rdict(schema_desc[1])
  invalid_count = 0
  impossible_count = 0

  # find mismatches
  for column_mapping in column_mappings.iteritems():
    found, expected = \
      itertools.starmap(dict.__getitem__,
        itertools.izip(schema_desc, column_mapping))
    assert found is schema_desc[0][column_mapping[0]]
    assert expected is schema_desc[1][column_mapping[1]]
    if found != expected:
      invalid_count += 0
      if found not in rschema_desc1:
        impossible_count += 1
        expected = None
    print('found {2} => {3}, expected {2} => {0} -- {1}'.format(
      expected, 'ok' if found == expected else 'MISMATCH!', *column_mapping))

  # find missing matches
  missing_count = len(schema_desc[0]) - len(column_mappings)
  if missing_count > 0:
    missing_count = 0
    missed_mappings = itertools.ifilterfalse(
      column_mappings.__contains__, schema_desc[0].iteritems())
    missed_mappings = utilities.teemap(
      missed_mappings, None, rschema_desc1.get)
    missed_mappings = itertools.ifilterfalse(
        utilities.composefn(utilities.second, utilities.isnone), # rule out impossible mappings
        missed_mappings)
    for missing in missed_mappings:
      print('expected {} => {} -- MISSED!'.format(*missing))
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
    itertools.imap(utilities.composefn(offset.__add__, str), column_mappings)
  ]
  if reversed:
    column_mappings.reverse()
  print(*itertools.starmap(','.join, itertools.izip(*column_mappings)), sep='\n')


if __name__ == '__main__':
  sys.exit(main(*sys.argv[1:]))
