#!/usr/bin/env python

import base
import port


def reload_modules():
    """Reload manipulator modules.

    This function reloads manipulator modules to reflect possible bug fixes on
    manipulator code.

    **HOWEVER, BEWARE -- THIS IS QUITE TRICKY!!**

    See the `kcsapi` module document for details. In short, be sure to reload
    modules starting from a module containing superclasses referenced from
    other modules.
    """
    import logging
    logger = logging.getLogger('kcaa.manipulator')
    # So, here are the modules referenced by other modules, in this order.
    # If a module A contains a class definition referenced in another module B,
    # the module A should precede B. (Or it **MUST** if the classes rely on
    # deriving relationship.)
    referenced_modules = [base]
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
    doctest.testmod(base)
    doctest.testmod(port)
    import os.path
    import pytest
    pytest.main(args=[os.path.dirname(__file__)])


if __name__ == '__main__':
    main()