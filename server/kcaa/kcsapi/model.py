#!/usr/bin/env python
"""JSON serializable object and properties.

This module contains some basic model of all KCAA objects, which are handled in
the controller, or transmitted to the client.
"""

import jsonobject
from jsonobject import jsonproperty


class KCAAObject(jsonobject.JSONSerializableObject):

    def __init__(self, api_name, response, debug, **kwargs):
        super(KCAAObject, self).__init__(**kwargs)
        self.api_names = set()
        self.debug = debug
        self.update(api_name, response)

    @jsonproperty
    def object_type(self):
        return self.__class__.__name__

    @jsonproperty(name='_api_names')
    def debug_api_names(self):
        if self.debug:
            return sorted(list(self.api_names))

    @jsonproperty(name='_raw_response')
    def debug_raw_response(self):
        if self.debug:
            return self.response

    def update(self, api_name, response):
        self.api_names.add(api_name)
        if self.debug:
            self.response = response


class DefaultObject(KCAAObject):

    @jsonproperty
    def object_type(self):
        return list(self.api_names)[0]

    def update(self, api_name, response):
        super(DefaultObject, self).update(api_name, response)
        assert len(self.api_names) == 1


class DefaultHandler(object):

    def __init__(self, api_name):
        self.api_name = api_name

    @property
    def __name__(self):
        return self.api_name

    def __call__(self, *args, **kwargs):
        return DefaultObject(*args, **kwargs)


class NullHandler(object):
    """Create a handler that does nothing.

    This handler is useful when you want to simply ignore a specific KCSAPI
    reponse. With this handler no new button will pollute the KCAA debug
    control window.
    """

    @property
    def __name__(self):
        return self.__class__.__name__

    def __call__(self, *args, **kwargs):
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
