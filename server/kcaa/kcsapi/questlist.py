#!/usr/bin/env python

import jsonobject
import model
import resource


class Quest(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """ID."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Name."""
    description = jsonobject.ReadonlyJSONProperty('description',
                                                  value_type=unicode)
    """Description."""
    category = jsonobject.ReadonlyJSONProperty('category', value_type=int)
    """Category."""
    CATEGORY_ORGANIZING = 1
    CATEGORY_EXPEDITION = 2
    CATEGORY_PRACTICE = 3
    CATEGORY_MISSION = 4
    CATEGORY_LOGISTICS = 5
    CATEGORY_SHIPYARD = 6
    CATEGORY_REBUILDING = 7
    state = jsonobject.ReadonlyJSONProperty('state', value_type=int)
    """State."""
    STATE_INACTIVE = 1
    STATE_ACTIVE = 2
    STATE_COMPLETE = 3
    progress = jsonobject.ReadonlyJSONProperty('progress', value_type=int)
    """Progress percentile."""
    bonus_type = jsonobject.ReadonlyJSONProperty('bonus_type', value_type=int)
    """Bonus type."""
    # TODO: Investigate what these values mean. Probably what kind of bonus
    # items can be obtained.
    cycle = jsonobject.ReadonlyJSONProperty('cycle', value_type=int)
    """Repop cycle."""
    CYCLE_ONCE = 1
    CYCLE_DAILY = 2
    CYCLE_WEEKLY = 3
    rewards = jsonobject.ReadonlyJSONProperty('rewards',
                                              value_type=resource.Resource)
    """Rewards."""


class QuestList(model.KCAAObject):
    """List of quests.

    This object holds a list of all the quests. Note that this object may not
    be up to date when a user hasn't accessed the quests page.
    """

    count = jsonobject.JSONProperty('count', value_type=int)
    """Number of all quests."""
    count_undertaken = jsonobject.JSONProperty('count_undertaken',
                                               value_type=int)
    """Number of quests undertaken."""
    quests = jsonobject.JSONProperty('quests', [], value_type=list,
                                     element_type=Quest)
    """Quest instances."""

    def update(self, api_name, request, response, objects, debug):
        super(QuestList, self).update(api_name, request, response, objects,
                                      debug)
        data = jsonobject.parse(response['api_data'])
        self.count = data.api_count
        self.count_undertaken = data.api_exec_count
        quests = []
        for quest_data in data.api_list:
            if quest_data == -1:
                continue
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
                rewards=resource.Resource(
                    fuel=quest_data.api_get_material[0],
                    ammo=quest_data.api_get_material[1],
                    steel=quest_data.api_get_material[2],
                    bauxite=quest_data.api_get_material[3])))
        quests.sort(lambda x, y: x.id - y.id)
        self.quests = model.merge_list(self.quests, quests)
