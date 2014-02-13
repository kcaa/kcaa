#!/usr/bin/env python

import model


class QuestList(model.KcaaObject):

    def __init__(self, api_name, response, debug):
        super(QuestList, self).__init__(api_name, response, debug)

    def update(self, api_name, result):
        super(QuestList, self).update(api_name, result)

    @property
    def data(self):
        data = {
        }
        return super(QuestList, self).format_data(data)
