#!/usr/bin/env python

import jsonobject
import model
import questlist


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
    documentation.) Here,  we see that B' is not a  subclass of A', which
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
    referenced_modules = [jsonobject, model]
    for module in referenced_modules:
        reload(module)
        logger.info('Reloaded module {}'.format(module.__name__))
    # Now, the rest of imported modules are safe to reload in an arbitrary
    # order.
    import types
    for key, value in globals().items():
        if (isinstance(value, types.ModuleType) and
                value not in referenced_modules):
            reload(value)
            logger.info('Reloaded module {}'.format(value.__name__))


def main():
    import doctest
    doctest.testmod(jsonobject)
    doctest.testmod(model)
    doctest.testmod(questlist)
    import os.path
    import pytest
    pytest.main(args=[os.path.dirname(__file__)])


if __name__ == '__main__':
    main()
