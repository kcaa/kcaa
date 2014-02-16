#!/usr/bin/env python

import jsonobject
import model


class QuestList(model.KcaaObject):

    count = jsonobject.JSONProperty('count')
    """Number of all quests."""
    count_undertaken = jsonobject.JSONProperty('count_undertaken')
    """Number of quests undertaken."""
    quests = jsonobject.JSONProperty('quests', default={})
    """Quest instances."""

    def update(self, api_name, response):
        super(QuestList, self).update(api_name, response)
        data = response['api_data']
        self.count = data['api_count']
        self.count_undertaken = data['api_exec_count']
        # TODO: Remove old quests? There may be another KCSAPI to remove
        # completed ones. Not sure for timed out ones.
        for quest_data in data['api_list']:
            quest = Quest(
                id=quest_data['api_no'],
                name=quest_data['api_title'],
                description=quest_data['api_detail'],
                rewards={
                    'oil': quest_data['api_get_material'][0],
                    'ammo': quest_data['api_get_material'][1],
                    'steel': quest_data['api_get_material'][2],
                    'bauxite': quest_data['api_get_material'][3]})
            self.quests[quest.id] = quest


class Quest(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id')
    """ID."""
    name = jsonobject.ReadonlyJSONProperty('name')
    """Name."""
    description = jsonobject.ReadonlyJSONProperty('description')
    """Description."""
    rewards = jsonobject.ReadonlyJSONProperty('rewards')
