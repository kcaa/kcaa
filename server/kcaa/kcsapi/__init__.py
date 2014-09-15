#!/usr/bin/env python

import battle
import client
import expedition
import fleet
import jsonobject
import mission
import model
import practice
import prefs
import quest
import repair
import resource
import ship


def is_class_object(attr, name):
    # Why no quick, easy and stable measure to do this?
    return (isinstance(attr, object) and
            name[0].isupper() and
            (hasattr(attr, '__dict__') or hasattr(attr, '__slots__')))


def expand_modules():
    import logging
    import types
    logger = logging.getLogger('kcaa.kcsapi')
    public_classes = {}
    for module in globals().itervalues():
        if not isinstance(module, types.ModuleType):
            continue
        class_names = []
        for name in dir(module):
            attr = getattr(module, name)
            if not is_class_object(attr, name):
                continue
            if (name in public_classes and
                    public_classes[name].__name__ != attr.__name__):
                raise TypeError('Name collision in kcsapi: {} and {}'.format(
                    repr(public_classes[name]), repr(attr)))
            public_classes[name] = attr
            class_names.append(name)
        logger.info('Expanded module {}: {}'.format(
            module.__name__, ', '.join(class_names)))
    for name, public_class in public_classes.iteritems():
        globals()[name] = public_class


def reload_modules():
    """Reload KCSAPI handler modules.

    This function reloads KCSAPI handler modules to reflect possible bug fixes
    on handler code.

    **HOWEVER, BEWARE -- THIS IS QUITE TRICKY!!**

    TL;DR: Be sure to reload modules starting from a module containing
    superclasses referenced from other modules.

    Suppose class B in module beta is derived from class A in module alpha.
    If we reload the module beta, a new class object B' is created, which
    subclasses A. Note that class B' is different from B, even if the textual
    definitions are completely identical.

    Then we reload the module alpha, and a new class object A' is created.
    What about B'? **IT STILL SUBCLASSES CLASS A, NOT A'!!** (this is
    mentioned in the last sentence of `reload()`_ built-in function
    documentation.) Here, we see that B' is not a  subclass of A', which
    will make `issubclass(B', A')` to be False and `super(A', <B' object>)`
    to raise TypeError. Beware that, in literal Python source file, the code
    reads `issubclass(B, A)` and `super(A, <B object>)` which looks good...
    but is actually bad.

    Possible solutions are:
    - Recreate class objects dynamically after all modules are reloaded
    - Reload from modules referenced from other modules
    And the latter should be much simpler than the former.

    .. _reload(): http://docs.python.org/2.7/library/functions.html#reload
    """
    import logging
    logger = logging.getLogger('kcaa.kcsapi')
    # So, here are the modules referenced by other modules, in this order.
    # If a module A contains a class definition referenced in another module B,
    # the module A should precede B. (Or it **MUST** if the classes rely on
    # deriving relationship.)
    referenced_modules = [jsonobject, model, resource]
    for module in referenced_modules:
        reload(module)
        logger.info('Reloaded module {}'.format(module.__name__))
    # Now, the rest of imported modules are safe to reload in an arbitrary
    # order.
    import types
    for module in globals().itervalues():
        if (not isinstance(module, types.ModuleType) or
                module in referenced_modules):
            continue
        reload(module)
        logger.info('Reloaded module {}'.format(module.__name__))
    expand_modules()


expand_modules()


def main():
    import doctest
    doctest.testmod(battle)
    doctest.testmod(client)
    doctest.testmod(expedition)
    doctest.testmod(fleet)
    doctest.testmod(jsonobject)
    doctest.testmod(mission)
    doctest.testmod(model)
    doctest.testmod(practice)
    doctest.testmod(prefs)
    doctest.testmod(quest)
    doctest.testmod(repair)
    doctest.testmod(resource)
    doctest.testmod(ship)
    import pytest
    import sys
    sys.exit(pytest.main())


if __name__ == '__main__':
    main()
