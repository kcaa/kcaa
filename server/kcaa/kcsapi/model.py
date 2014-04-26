#!/usr/bin/env python
"""JSON serializable object and properties.

This module contains some basic model of all KCAA objects, which are handled in
the controller, or transmitted to the client.
"""

import jsonobject
from jsonobject import jsonproperty


class RawTransaction(jsonobject.JSONSerializableObject):
    """Raw transaction data."""

    request = jsonobject.JSONProperty(
        'request', value_type=jsonobject.JSONSerializableObject)
    """Raw request."""
    response = jsonobject.JSONProperty(
        'response', value_type=jsonobject.JSONSerializableObject)
    """Raw response."""


class KCAAObject(jsonobject.JSONSerializableObject):

    _raw_transactions = jsonobject.JSONProperty('_raw_transactions',
                                                value_type=dict)
    generation = jsonobject.JSONProperty('generation', 0, value_type=int)
    """Generation of the object.

    This field starts with 0, and is incremented every time it detects a KCSAPI
    request that updates this object.

    This value is incremented even if the object contents don't change. If you
    need an incremental update, use DifferentialKCAAObject.
    TODO: Create DifferentialKCAAObject.
    """

    @jsonproperty
    def object_type(self):
        return self.__class__.__name__

    def update(self, api_name, request, response, objects, debug):
        if debug:
            if not self._raw_transactions:
                self._raw_transactions = {}
            self._raw_transactions[api_name] = RawTransaction(
                request=request,
                response=response)


class DefaultObject(KCAAObject):

    @jsonproperty
    def object_type(self):
        return self._raw_transactions.keys()[0]

    def update(self, api_name, request, response, objects, debug):
        super(DefaultObject, self).update(api_name, request, response, objects,
                                          True)
        assert len(self._raw_transactions) == 1


class DefaultHandler(object):

    def __init__(self, api_name):
        self.api_name = api_name

    @property
    def __name__(self):
        return self.api_name

    def __call__(self):
        return DefaultObject()


class NullHandler(object):
    """Create a handler that does nothing.

    This handler is useful when you want to simply ignore a specific KCSAPI
    reponse. With this handler no new button will pollute the KCAA debug
    control window.
    """

    @property
    def __name__(self):
        return self.__class__.__name__

    def __call__(self):
        return None


def merge_list(old_list, new_list):
    merged = []
    if len(old_list) == 0:
        return new_list
    elif len(new_list) == 0:
        return old_list
    a, b = old_list, new_list
    bmin, bmax = b[0].id, b[-1].id
    ai, bi = 0, 0
    while ai < len(a) and bi < len(b):
        aid, bid = a[ai].id, b[bi].id
        # If a and b have the same ID, prefer b (new quest data).
        if aid == bid:
            merged.append(b[bi])
            ai += 1
            bi += 1
        elif aid < bid:
            # Exclude old quests.
            if aid < bmin or aid > bmax:
                merged.append(a[ai])
            ai += 1
        else:
            merged.append(b[bi])
            bi += 1
    if ai == len(a):
        merged.extend(b[bi:])
    else:
        merged.extend(a[ai:])
    return merged


if __name__ == '__main__':
    import model_test
    model_test.main()
