#!/usr/bin/env python

import model


class QuestList(model.KcaaObject):

    def __init__(self, api_name, response, debug):
        self.quests = {}
        super(QuestList, self).__init__(api_name, response, debug)

    def update(self, api_name, response):
        super(QuestList, self).update(api_name, response)
        data = response['api_data']
        # Number of all quests.
        self.count = data['api_count']
        # Number of quests undertaken.
        self.count_undertaken = data['api_exec_count']
        # Quest instances.
        self.quests.update({quest_data['api_no']: Quest(quest_data) for
                            quest_data in data['api_list']})

    @property
    def data(self):
        return super(QuestList, self).format_data({
            'count': self.count,
            'count_undertaken': self.count_undertaken,
            'quests': [self.quests[key].data for key in
                       sorted(self.quests.keys())],
        })


class Quest(object):

    def __init__(self, data):
        # ID.
        self.id = data['api_no']
        # Name.
        self.name = data['api_title']
        # Description.
        self.description = data['api_detail']
        # Reward materials.
        self.rewards = {
            'oil': data['api_get_material'][0],
            'ammo': data['api_get_material'][1],
            'steel': data['api_get_material'][2],
            'bauxite': data['api_get_material'][3],
        }

    @property
    def data(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rewards': self.rewards,
        }
