#!/usr/bin/env python
"""JSON serializable object and properties.

This module contains some basic model of all KCAA objects, which are handled in
the controller, or transmitted to the client.
"""

import datetime
import time

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

    def clean_copy(self):
        # TODO: Test and document.
        clean_dict = self.convert_to_dict()
        if '_raw_transactions' in clean_dict:
            del clean_dict['_raw_transactions']
        obj = self.__class__.parse(clean_dict)
        obj.generation = None
        return obj


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


class JournalEntry(jsonobject.JSONSerializableObject):

    time = jsonobject.JSONProperty('time', value_type=long)
    """Time of this entry."""

    @classmethod
    def typed(cls, value_type):
        return type(
            'JournalEntry__{}'.format(value_type.__name__), (cls,),
            {'value': jsonobject.JSONProperty('value', value_type=value_type)})


class KCAAJournalObject(KCAARequestableObject):

    @classmethod
    def typed(cls, value_type):
        entry_type = JournalEntry.typed(value_type)
        return type(
            'KCAAJournalObject__{}'.format(entry_type.__name__), (cls,),
            {'entries': jsonobject.JSONProperty('entries', [], value_type=list,
                                                element_type=entry_type),
             'Entry': entry_type})

    def __init__(self, *args, **kwargs):
        super(KCAAJournalObject, self).__init__(*args, **kwargs)
        if not self.monitored_objects:
            raise ValueError(
                'Journal {} has 0 monitored object, but needs at least 1'
                .format(self.object_type))
        if not self.retention_policy:
            raise ValueError('No retention policy is defined.')
        last_policy = (datetime.timedelta(seconds=0), None)
        for policy in self.retention_policy:
            if len(policy) != 2 or policy[0] <= last_policy[0]:
                raise ValueError('Invalid retention policy: {}'.format(
                    repr(policy)))
        self._last_generations = {name: 0 for name in self.monitored_objects}

    @jsonproperty
    def object_type(self):
        return self.__class__.__name__

    @property
    def monitored_objects(self):
        return []

    @property
    def retention_policy(self):
        """Returns the retention policy of this journal.

        The retention policy is defined as the list of policy objects. A policy
        object is a pair of :class:`datetime.timedelta` objects; the first
        represents the time window, and the latter for the interval.

        Policy objects must be sorted in the ascending order of the time
        window.
        """
        return [
            (datetime.timedelta(hours=6), datetime.timedelta(minutes=5)),
            (datetime.timedelta(days=1), datetime.timedelta(minutes=30)),
            (datetime.timedelta(days=7), datetime.timedelta(hours=2)),
            (datetime.timedelta(days=30), datetime.timedelta(hours=6)),
            (datetime.timedelta.max, datetime.timedelta(days=1)),
        ]

    def add_entry(self, value):
        now = long(time.time())
        if self._is_acceptable_interval(now)[0]:
            self.entries.append(self.Entry(time=now, value=value))
            return True
        return False

    def clean_up_old_entries(self):
        # TODO: Test.
        old_entries = self.entries
        self.entries = []
        now = long(time.time())
        last_entry = None
        penalty = None
        for entry in old_entries:
            acceptable, penalty = self._is_acceptable_interval(
                now, entry.time, last_entry, penalty)
            if acceptable:
                self.entries.append(entry)
                last_entry = entry
        return len(self.entries)

    def _is_acceptable_interval(self, now, entry_time=None, last_entry=None,
                                penalty=None):
        # TODO: Test.
        penalty = penalty if penalty else datetime.timedelta(seconds=0)
        entry_time = entry_time if entry_time else now
        policy = self._get_retention_policy(now, entry_time)
        if not policy:
            return False, penalty
        if not self.entries:
            return True, penalty
        last_entry = last_entry if last_entry else self.entries[-1]
        seconds_delta = entry_time - last_entry.time
        delta = datetime.timedelta(seconds=seconds_delta) - penalty
        if delta >= policy[1]:
            return True, 0
        elif delta > 9 * policy[1] / 10:
            # Allow a small overrunning with penalty carryover.
            return True, policy[1] - delta
        else:
            return False, penalty

    def _get_retention_policy(self, now, entry_time):
        delta = datetime.timedelta(seconds=(now - entry_time))
        for policy in self.retention_policy:
            if delta < policy[0]:
                return policy
        # No policy found. The entry should not retained any longer.
        return None

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
