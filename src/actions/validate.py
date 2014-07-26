import sys, os.path, operator
from math import fsum
from operator import itemgetter
import utilities
from utilities.iterator import sort_by_order
from utilities.functional import memberfn
from .match import collect_analyse_match



def validate(schema_instances, collectorset_description, **kwargs):
  _, _, best_matches, stats = \
    validate_stats(schema_instances, collectorset_description, **kwargs)

  if len(best_matches) > 1:
    possible_count = stats[0] + stats[1]
    avg_norm = fsum(map(itemgetter(2), best_matches)) / len(best_matches)
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
      tuple(sort_by_order(schema_instances, sort_order))
  print_total = len(best_matches) > 1
  counts = (
    validate_result(
      (schema_instances[c1_idx].name, schema_instances[c2_idx].name),
      best_match, best_match_norm, print_total, **kwargs)
    for c1_idx, c2_idx, best_match_norm, best_match in best_matches)
  return (collectors, sort_order, best_matches, tuple(map(sum, zip(*counts))))


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
