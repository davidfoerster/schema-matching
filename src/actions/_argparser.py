import sys, argparse, utilities.argparse, collector.description


p = argparse.ArgumentParser(
  formatter_class=utilities.argparse.CombinedCustomHelpFormatter,
  description="Match data schema attributes.")

action_group = p.add_mutually_exclusive_group(required=True)
def add_action(name, max_collectorset_descriptions, shortopt='-', help=None):
  flags = ['--' + name]
  if shortopt is not None:
    if shortopt == '-':
      shortopt = name[0].upper()
    assert len(shortopt) == 1 and shortopt.isalpha()
    flags.insert(0, '-' + shortopt)
  return action_group.add_argument(
    *flags, dest='action', action='store_const', help=help,
    const=(name.replace('-', '_'), max_collectorset_descriptions))

add_action('match', 1, help=
  "Tries to match the attributes/columns of two schema instances to each "
  "other.")
add_action('validate', 1, help=
  "Validates a discovered schema instance mapping against corresponding known "
  "schema mappings from files '${SCHEMA-INSTANCE%%.*}_desc.txt' to a common "
  "abstract source schema and prints statistics about the discovered vs. the "
  "expected mapping(s). Multiple schema instances (≥2) are supported.\n"
  "The mapping description is expected to consist of lines "
  "of comma-delimited pairs of positive integers, where each pair 'I,J' "
  "describes a mapping of column attribute I in the corresponding schema "
  "instance to column attribute J in the source schema.")
add_action('compare-descriptions', -1, help=
  "Compares and ranks the validation results of multiple COLLECTORSET-"
  "DESCRIPTIONs.")

p.add_argument('schema_instances', nargs=range(2, sys.maxsize),
  type=argparse.FileType('r'), action=utilities.argparse.NargsRangeAction,
  metavar='SCHEMA-INSTANCE', help=
  "The path to a delimited (e. g. CSV) file of records conforming to an "
  "(unknown) schema")
p.add_argument('-d', '--desc', action='append', dest='collectorset_descriptions',
  metavar='(:MODULENAME | MODULEFILE)', type=collector.description.argparser,
  help=
  "A reference to a python module either by file path or module name "
  "(starting with a ':' character), with two global attributes:\n"
  "  'descriptions' - (mandatory) A set or sequence of attribute collector "
      "templates; either an ItemCollector subclass, instance, or factory.\n"
  "  'weights' - (optional) A dictionary assigning weight coefficients or "
      "functions to collector classes. You should probably use an instance "
      "of WeightDict. For examples see the modules in the "
      "collector.descriptions package.\n"
  "Some modes of operation allow or require multiple descriptions, that can "
  "be specified by multiple occurrences of this option. (default: "
  "collector.descriptions.default)")
p.add_argument('-o', '--output', type=argparse.FileType('w'),
  default=sys.stdout, metavar='FILE', help=
  "Target file for the results of the program; defaults to the standard "
  "output")
p.add_argument('--time-limit', type=int, choices=range(sys.maxsize),
  default=0, metavar='SECONDS', help=
  "If running 'match' mode takes longer than %(metavar)s, the program is "
  "interrupted and its results up to that point written to the output "
  "destination. '0' means unrestricted time (default).")
p.add_argument('--field-delimiter', metavar='DELIM', default=';', help=
  "The field delimiter of SCHEMA-INSTANCEs (default: '%(default)s')")
p.add_argument('--number-format', metavar='FORMAT', default='.3e', help=
  "Number format for real values in collector data and statistics; only for "
  "higher verbosity levels (default: '%(default)s')")
p.add_argument('-v', '--verbose', action='count', default=int(__debug__),
  help="Increase the amount detail of the program output on the standard "
  "error output. Can be specified multiple times to raise the verbosity "
  "level further. Currently implemented levels:\n"
  "\t1 - some useful intermediate results and warnings about problematic "
    "schema instance records.\n"
  "\t2 - detailed intermediate results.\n"
  "(default: %(default)d)")
