import utilities


def parse(src):
  if src == ':':
    from ..description import default as desc
  elif src.startswith(':'):
    import importlib
    desc = importlib.import_module(src[1:])
  else:
    import os, imp
    from .. import description as parent_package # needs to be imported before its child modules
    with open(src) as f:
      module_name = \
        '{0}._anonymous_{1.st_dev}_{1.st_ino}'.format(
          parent_package.__name__, os.fstat(f.fileno()))
      desc = imp.load_source(module_name, src, f)
    assert isinstance(getattr(desc, '__file__', None), str)

  utilities.setattr_default(desc, '__file__', '<unknown file>')
  if not hasattr(desc, 'descriptions'):
    raise NameError(
      "The collector description module doesn't contain any collector description.",
      desc, desc.__file__,
      "missing attribute 'descriptions'")

  return desc
