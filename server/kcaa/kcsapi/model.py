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

    This value is incremented even if the object contents don't change by
    default. To disable this, override :meth:`auto_generation` and return False
    and increment :attr:`generation` by yourself.
    """

    @jsonproperty
    def object_type(self):
        return self.__class__.__name__

    @property
    def auto_generation(self):
        return True

    def update(self, api_name, request, response, objects, debug):
        if self.auto_generation:
            self.generation += 1
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


class KCAARequestableObject(jsonobject.JSONSerializableObject):

    @jsonproperty
    def object_type(self):
        return self.__class__.__name__

    @property
    def required_objects(self):
        return []

    def _request(self, objects, **kwargs):
        for required_object in self.required_objects:
            if required_object not in objects:
                return None
        object_args = {translate_object_name(name): objects[name] for name in
                       self.required_objects}
        for key in kwargs:
            if key in object_args:
                raise ValueError(
                    'Requestable {} got a conflicting parameter with required '
                    'objects: {}'.format(self.object_type, key))
        object_args.update(kwargs)
        return self.request(**object_args)


class KCAAJournalObject(KCAARequestableObject):

    def __init__(self, *args, **kwargs):
        super(KCAAJournalObject, self).__init__(*args, **kwargs)
        if not self.monitored_objects:
            raise ValueError(
                'Journal {} has 0 monitored object, but needs at least 1'
                .format(self.object_type))
        self._last_generations = {name: 0 for name in self.monitored_objects}

    @jsonproperty
    def object_type(self):
        return self.__class__.__name__

    @property
    def monitored_objects(self):
        return []

    def _update(self, api_names, objects):
        has_updates, updates = self.get_object_generation_updates(objects)
        if not has_updates:
            return
        self.update_generations(updates)
        object_args = {translate_object_name(name): objects[name] for name in
                       self.monitored_objects}
        self.update(api_names, **object_args)

    def get_object_generation_updates(self, objects):
        generation_updates = {}
        updated = False
        for req_obj_name in self.monitored_objects:
            obj = objects.get(req_obj_name)
            if obj is None:
                return False, {}
            if obj.generation > self._last_generations[req_obj_name]:
                generation_updates[req_obj_name] = obj.generation
                updated = True
        return updated, generation_updates

    def update_generations(self, updates):
        self._last_generations.update(updates)


def translate_object_name(object_name):
    result_name = ''
    for c in object_name:
        if c.isupper() and result_name:
            result_name += '_'
        result_name += c.lower()
    return result_name


def merge_list(old_list, new_list):
    """Merge the given 2 lists.

    :param list old_list: list which contains old items
    :param list new_list: list which contains new items
    :returns: merged list

    Merges the given 2 lists into 1 list, preferring items from *new_list* when
    collide.

    An item in the lists should have a field named *id*.
    """
    merged = []
    if len(old_list) == 0:
        return new_list
    elif len(new_list) == 0:
        return old_list
    a, b = old_list, new_list
    ai, bi = 0, 0
    while ai < len(a) and bi < len(b):
        aid, bid = a[ai].id, b[bi].id
        # If a and b have the same ID, prefer b (new data).
        if aid == bid:
            merged.append(b[bi])
            ai += 1
            bi += 1
        elif aid < bid:
            # Do not exclude old items even when interpolating.
            # Such a removal should be done explicitly by KCSAPI handlers.
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
