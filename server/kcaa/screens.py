#!/usr/bin/env python
"""Screen type definitions."""


UNKNOWN = 0
SPECIAL = 1
SPECIAL_START = 101
PORT = 2
PORT_MAIN = 200
PORT_RECORD = 201
PORT_ENCYCLOPEDIA = 202
PORT_ITEMRACK = 203
PORT_FURNITURE = 204
PORT_QUESTLIST = 205
PORT_ITEMSHOP = 206
PORT_EXPEDITION = 207
PORT_PRACTICE = 208
PORT_MISSION = 209
PORT_ORGANIZING = 210
PORT_LOGISTICS = 211
PORT_REBUILDING = 212
PORT_REPAIR = 213
PORT_SHIPYARD = 214
PRACTICE = 4
PRACTICE_BATTLE = 400
PRACTICE_BATTLERESULT = 401
MISSION = 5
MISSION_RESULT = 500


def in_category(screen, category):
    while screen > category:
        screen /= 100
    return screen == category
