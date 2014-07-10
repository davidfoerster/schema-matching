#!/usr/bin/python
from __future__ import print_function
import csv, sys, os.path, itertools, operator, math
import utilities, utilities.file
from utilities import infinity
from utilities.string import DecodableUnicode
import utilities.iterator as uiterator
import utilities.functional as ufunctional
import collector, collector.columntype
from collector import MultiphaseCollector
from collector.columntype import ColumnTypeItemCollector
from collector.itemaverage import ItemAverageCollector
from collector.letteraverage import ItemLetterAverageCollector
from collector.variance import ItemStandardDeviationCollector
from collector.lettervariance import LetterStandardDeviationCollector
from collector.relativeletterfrequency import ItemLetterRelativeFrequencyCollector


number_format = '10.4e'

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
  must_validate = False

  # determine mode and/or output file
  if len(argv) > 2:
    if argv[2] == '--validate':
      must_validate = True
    else:
      sys.stdout = utilities.file.openspecial(argv[2], 'w')

  # determine collector weights to use
  if len(argv) > 3:
    with utilities.file.openspecial(argv[3], 'rb') as f:
      import pickle
      weights = pickle.load(f)
  else:
    weights = collector_weights


  # collect from both input files
  collectors = [collect(path, *collector_phase_description) for path in in_paths]

  # The first collector shall have the least columns.
  isreversed = len(collectors[0].merged_predecessors) > len(collectors[1].merged_predecessors)
  if isreversed:
    collectors.reverse()
    in_paths.reverse()

  # analyse collected data
  norms = MultiphaseCollector.results_norms(*collectors, weights=weights)
  if __debug__:
    print(*reversed(in_paths), sep=' / ', end='\n| ', file=sys.stderr)
    formatter = ufunctional.apply_memberfn(format, number_format)
    print(
      *['  '.join(itertools.imap(formatter, row)) for row in norms],
      sep=' |\n| ', end=' |\n\n', file=sys.stderr)

  # find minimal combination
  best_match = get_best_schema_mapping(norms)

  # print or validate best match
  if must_validate:
    validation_result = validate_result(in_paths, best_match[1], isreversed)
    print('\n{2} invalid, {3} impossible, and {4} missing matches, norm = {0:{1}}'.format(
      best_match[0], number_format, *validation_result))
    return int(validation_result[0] or validation_result[2])

  else:
    print('norm:', format(best_match[0], number_format), file=sys.stderr)
    print_result(best_match[1], isreversed)
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

  with open(path, 'rb') as f:
    reader = csv.reader(f, delimiter=';', skipinitialspace=True)
    reader = itertools.imap(
      lambda list: uiterator.map_inplace(lambda item: DecodableUnicode(item.strip()), list),
      reader)
    multiphasecollector = MultiphaseCollector(reader)

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


def validate_result(in_paths, found_mappings, reversed=False, offset=1):
  """
  :param in_paths: list[str]
  :param found_mappings: list[int]
  :param reversed: bool
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
        in itertools.imap(ufunctional.apply_memberfn(str.split, ',', 2), f)
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
