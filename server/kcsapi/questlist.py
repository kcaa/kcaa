#!/usr/bin/env python

import model


class QuestList(model.KcaaObject):

    def update(self, api_name, response):
        super(QuestList, self).update(api_name, response)

    @property
    def data(self):
        data = {
        }
        return super(QuestList, self).format_data(data)
