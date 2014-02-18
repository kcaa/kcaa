#!/usr/bin/env python

import jsonobject
import model


class Quest(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', 0, value_type=int)
    """ID."""
    name = jsonobject.ReadonlyJSONProperty('name', u'', value_type=unicode)
    """Name."""
    description = jsonobject.ReadonlyJSONProperty('description', u'',
                                                  value_type=unicode)
    """Description."""
    rewards = jsonobject.ReadonlyJSONProperty('rewards', {}, value_type=dict)
    """Rewards."""
    # TODO: Add Rewards object


class QuestList(model.KcaaObject):

    count = jsonobject.JSONProperty('count', 0, value_type=int)
    """Number of all quests."""
    count_undertaken = jsonobject.JSONProperty('count_undertaken', 0,
                                               value_type=int)
    """Number of quests undertaken."""
    quests = jsonobject.JSONProperty('quests', [], value_type=list,
                                     element_type=Quest)
    """Quest instances."""
    # TODO: Make this a list, not a map.

    def update(self, api_name, response):
        super(QuestList, self).update(api_name, response)
        data = jsonobject.parse(response['api_data'])
        self.count = data.api_count
        self.count_undertaken = data.api_exec_count
        quests = []
        for quest_data in data.api_list:
            quests.append(Quest(
                id=quest_data.api_no,
                name=quest_data.api_title,
                description=quest_data.api_detail,
                rewards={
                    'oil': quest_data.api_get_material[0],
                    'ammo': quest_data.api_get_material[1],
                    'steel': quest_data.api_get_material[2],
                    'bauxite': quest_data.api_get_material[3]}))
        quests.sort(lambda x, y: x.id - y.id)
        if len(self.quests) == 0:
            self.quests = quests
            return
        elif len(quests) == 0:
            return
        # Merge with existing quests.
        merged = []
        a, b = self.quests, quests
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
        self.quests = merged
