#!/usr/bin/env python

import jsonobject
import model


class Rewards(jsonobject.JSONSerializableObject):

    fuel = jsonobject.ReadonlyJSONProperty('fuel', 0, value_type=int)
    """Fuel."""
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
    CATEGORY_FORMULATION = 1
    CATEGORY_EXPEDITION = 2
    CATEGORY_PRACTICE = 3
    CATEGORY_MISSION = 4
    CATEGORY_LOGISTICS = 5
    CATEGORY_SHIPYARD = 6
    CATEGORY_REBUILDING = 7
    state = jsonobject.ReadonlyJSONProperty('state', 0, value_type=int)
    """State."""
    STATE_INACTIVE = 1
    STATE_ACTIVE = 2
    STATE_COMPLETE = 3
    progress = jsonobject.ReadonlyJSONProperty('progress', 0, value_type=int)
    """Progress percentile."""
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


class QuestList(model.KCAAObject):
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
                    fuel=quest_data.api_get_material[0],
                    ammo=quest_data.api_get_material[1],
                    steel=quest_data.api_get_material[2],
                    bauxite=quest_data.api_get_material[3])))
        quests.sort(lambda x, y: x.id - y.id)
        self.quests = model.merge_list(self.quests, quests)
