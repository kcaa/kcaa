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
PORT_REBUILDING_REBUILDRESULT = 21200
PORT_REBUILDING_REMODELRESULT = 21201
PORT_REPAIR = 213
PORT_SHIPYARD = 214
EXPEDITION = 3
EXPEDITION_COMPASS = 300
EXPEDITION_SAILING = 301
EXPEDITION_FORMATION = 302
EXPEDITION_COMBAT = 303
EXPEDITION_NIGHT = 304
EXPEDITION_NIGHTCOMBAT = 305
EXPEDITION_RESULT = 306
EXPEDITION_REWARDS = 307
EXPEDITION_CONTINUE = 308
EXPEDITION_TERMINAL = 309
PRACTICE = 4
PRACTICE_COMBAT = 400
PRACTICE_NIGHT = 401
PRACTICE_NIGHTCOMBAT = 402
PRACTICE_RESULT = 403
MISSION = 5
MISSION_RESULT = 500
SHIPYARD = 6
SHIPYARD_GETSHIP = 600
SHIPYARD_GETEQUIPMENT = 601


def in_category(screen, category):
    while screen > category:
        screen /= 100
    return screen == category
