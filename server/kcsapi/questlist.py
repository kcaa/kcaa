#!/usr/bin/env python

import model


class QuestList(model.KcaaObject):

    def __init__(self, response, debug):
        super(QuestList, self).__init__(response, debug)

    def update(self, result):
        super(QuestList, self).update(result)

    @property
    def data(self):
        data = {
        }
        return super(QuestList, self).format_data(data)
