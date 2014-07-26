#!/usr/bin/python3 -OO
import sys
import actions
from actions import argument_parser



def main(argv=None):
  opts = argument_parser.parse_args(argv)

  if opts.time_limit and opts.action[0] != 'match':
    print(
      "Warning: The time limit option doesn't work with the '", opts.action[0],
      "' action.",
      sep='', file=sys.stderr)

  dispatcher = (
      __single_collectorset_description_action
    if opts.action[1] == 1 else
      __multi_collectorset_description_action)
  return dispatcher(opts)


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

  return getattr(actions, action[0])(**options)


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

  return getattr(actions, action[0])(**options)


if __name__ == '__main__':
  sys.exit(main())
