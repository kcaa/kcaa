#!/usr/bin/env python

import model


class QuestList(model.KcaaObject):

    def __init__(self, api_name, response, debug):
        self._quests = {}
        super(QuestList, self).__init__(api_name, response, debug)

    def update(self, api_name, response):
        super(QuestList, self).update(api_name, response)
        data = response['api_data']
        # Number of all quests.
        self._count = data['api_count']
        # Number of quests undertaken.
        self._count_undertaken = data['api_exec_count']
        # Quest instances.
        # TODO: Remove old quests? There may be another KCSAPI to remove
        # completed ones. Not sure for timed out ones.
        self._quests.update({quest_data['api_no']: Quest(quest_data) for
                             quest_data in data['api_list']})

    @model.jsonproperty
    def count(self):
        return self._count

    @model.jsonproperty
    def count_undertaken(self):
        return self._count_undertaken

    @model.jsonproperty
    def quests(self):
        return self._quests


class Quest(model.JsonSerializableObject):

    def __init__(self, data):
        # ID.
        self._id = data['api_no']
        # Name.
        self._name = data['api_title']
        # Description.
        self._description = data['api_detail']
        # Reward materials.
        self._rewards = {
            'oil': data['api_get_material'][0],
            'ammo': data['api_get_material'][1],
            'steel': data['api_get_material'][2],
            'bauxite': data['api_get_material'][3],
        }

    @model.jsonproperty
    def id(self):
        return self._id

    @model.jsonproperty
    def name(self):
        return self._name

    @model.jsonproperty
    def description(self):
        return self._description

    @model.jsonproperty
    def rewards(self):
        return self._rewards
