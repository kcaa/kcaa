#!/usr/bin/env python

import jsonobject
import model


class Rewards(jsonobject.JSONSerializableObject):

    oil = jsonobject.ReadonlyJSONProperty('oil', 0, value_type=int)
    """Oil."""
    ammo = jsonobject.ReadonlyJSONProperty('ammo', 0, value_type=int)
    """Ammo."""
    steel = jsonobject.ReadonlyJSONProperty('steel', 0, value_type=int)
    """Steel."""
    bauxite = jsonobject.ReadonlyJSONProperty('bauxite', 0, value_type=int)
    """Bauxite."""


class Quest(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', 0, value_type=int)
    """ID."""
    name = jsonobject.ReadonlyJSONProperty('name', u'', value_type=unicode)
    """Name."""
    description = jsonobject.ReadonlyJSONProperty('description', u'',
                                                  value_type=unicode)
    """Description."""
    category = jsonobject.ReadonlyJSONProperty('category', 0, value_type=int)
    """Category."""
    CATEGORY_ORGANIZE = 1
    CATEGORY_ATTACK = 2
    state = jsonobject.ReadonlyJSONProperty('state', 0, value_type=int)
    """State."""
    progress = jsonobject.ReadonlyJSONProperty('progress', 0, value_type=int)
    """Progress percentile."""
    STATE_INACTIVE = 1
    STATE_ACTIVE = 2
    STATE_COMPLETE = 3
    bonus_type = jsonobject.ReadonlyJSONProperty('bonus_type', 0,
                                                 value_type=int)
    """Bonus type."""
    # TODO: Investigate what these values mean. Probably what kind of bonus
    # items can be obtained.
    cycle = jsonobject.ReadonlyJSONProperty('cycle', 0, value_type=int)
    """Repop cycle."""
    CYCLE_ONCE = 1
    CYCLE_DAILY = 2
    CYCLE_WEEKLY = 3
    rewards = jsonobject.ReadonlyJSONProperty('rewards', None,
                                              value_type=Rewards)
    """Rewards."""


class QuestList(model.KcaaObject):
    """List of quests.

    This object holds a list of all the quests. Note that this object may not
    be up to date when a user hasn't accessed the quests page.
    """

    count = jsonobject.JSONProperty('count', 0, value_type=int)
    """Number of all quests."""
    count_undertaken = jsonobject.JSONProperty('count_undertaken', 0,
                                               value_type=int)
    """Number of quests undertaken."""
    quests = jsonobject.JSONProperty('quests', [], value_type=list,
                                     element_type=Quest)
    """Quest instances."""

    def update(self, api_name, response):
        super(QuestList, self).update(api_name, response)
        data = jsonobject.parse(response['api_data'])
        self.count = data.api_count
        self.count_undertaken = data.api_exec_count
        quests = []
        for quest_data in data.api_list:
            progress = (0, 50, 80)[quest_data.api_progress_flag]
            if quest_data.api_state == Quest.STATE_COMPLETE:
                progress = 100
            quests.append(Quest(
                id=quest_data.api_no,
                name=quest_data.api_title,
                description=quest_data.api_detail,
                category=quest_data.api_category,
                state=quest_data.api_state,
                progress=progress,
                bonus_type=quest_data.api_bonus_flag,
                cycle=quest_data.api_type,
                rewards=Rewards(
                    oil=quest_data.api_get_material[0],
                    ammo=quest_data.api_get_material[1],
                    steel=quest_data.api_get_material[2],
                    bauxite=quest_data.api_get_material[3])))
        quests.sort(lambda x, y: x.id - y.id)
        # Merge with existing quests.
        self.merge_quests(quests)

    def merge_quests(self, quests):
        merged = []
        if len(self.quests) == 0:
            self.quests = quests
            return
        elif len(quests) == 0:
            return
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
