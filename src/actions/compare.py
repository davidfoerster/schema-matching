import sys, math
from operator import itemgetter
from utilities.functional import memberfn
from collector.multiphase import MultiphaseCollector
from .collect import read_schema_instance
from .validate import validate_stats



def compare_descriptions(schema_instances, collectorset_descriptions, **kwargs):
  assert len(collectorset_descriptions) >= 2
  out = kwargs.get('output', sys.stdout)

  collectors = sorted(
    map(memberfn(read_schema_instance, **kwargs), schema_instances),
    key=MultiphaseCollector.columncount)
  overall_stats = []

  for desc in collectorset_descriptions:
    _, _, best_matches, stats = validate_stats(
      tuple(map(MultiphaseCollector.copy, collectors)), desc, **kwargs)
    avg_norm = \
      math.fsum(map(itemgetter(2), best_matches)) / len(best_matches)
    overall_stats.append((desc, stats[1] + stats[2], avg_norm))
    print_description_comment(desc, out)

  overall_stats.sort(key=itemgetter(slice(1, 3)))
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


def print_description_comment(desc, out):
  print(
    "... with collector descriptions and weights from {0.__file__} "
    "({0.__name__}).".format(
      desc),
    end='\n\n', file=out)
