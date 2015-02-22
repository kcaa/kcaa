#!/usr/bin/env python

import base64
import logging
import os
import re
import traceback
import urlparse

import kcsapi


def reload_modules():
    reload(kcsapi)
    kcsapi.reload_modules()


KCSAPI_PATH_REGEX = re.compile(r'/kcsapi(?P<api_name>/.*)')
KCSAPI_PREFIX = 'svdata='

# UTF-8 Byte Order Mark.
BOM = '\xEF\xBB\xBF'


class KCSAPIHandler(object):

    def __init__(self, har_manager, journal_basedir, debug):
        self._logger = logging.getLogger('kcaa.kcsapi_util')
        self.har_manager = har_manager
        self.debug = debug
        self.objects = {}
        self.define_handlers()
        self.define_requestables()
        self.define_journals()
        self.load_journals(journal_basedir)

    def define_handlers(self):
        """Define KCSAPI handlers.

        For each KCSAPI, define proper handlers. The order matters; start from
        the independent ones, and then followed by depending ones. Otherwise a
        client may read an incomplete data. For 2 independent handlers, order
        them alphabetically.

        Precedence requirements:
        - RepairDock -> ShipList: needs to populate is_under_repair
        - ShipList -> FleetList: due to potential dependence

        The reason to define handlers here, not in a module level, is to
        refresh the handler class objects to reflect what's in source files
        under kcsapi/ directory.
        """
        # API URLs can be classified into 3 classes:
        # - /api_get_member/FOO: Get the current status about FOO. User
        #                        dependent. Some data is delivered through a
        #                        shared KCSAPI, /api_port/port.
        # - /api_req_FOO/BAR: Make changes on FOO by doing an action BAR.
        #                     Doesn't necessarily deliver useful information
        #                     in the response (i.e. oftentimes the request
        #                     itself is important).
        # - Others.
        self.kcsapi_handlers = {
            # Initialization, or account information.
            # /api_start2 now delivers most (all?) master information;
            # invariant data required for modelling, rendering and everything.
            '/api_auth_member/logincheck': [kcsapi.NullHandler()],
            '/api_req_member/get_incentive': [kcsapi.NullHandler()],
            '/api_start2': [kcsapi.MissionList,
                            kcsapi.ShipDefinitionList,
                            kcsapi.EquipmentDefinitionList],
            # Player info.
            '/api_get_member/basic': [kcsapi.player.PlayerInfo],
            # Resources.
            '/api_get_member/material': [kcsapi.player.PlayerResources],
            # Encyclopedia.
            '/api_get_member/picture_book': [kcsapi.NullHandler()],
            # Ships.
            '/api_get_member/ship2': [kcsapi.ShipList],
            '/api_get_member/ship3': [kcsapi.ShipList,
                                      kcsapi.FleetList],
            '/api_req_hensei/lock': [kcsapi.ShipList],
            '/api_req_hokyu/charge': [kcsapi.ShipList],
            # Port.
            # Like /api_start2, /api_port/port delivers most (all?) member
            # information; variant data for the player, ships, fleets, repair
            # or building docks.
            '/api_port/port': [kcsapi.MissionList,
                               kcsapi.RepairDock,
                               kcsapi.ShipList,
                               kcsapi.FleetList,
                               kcsapi.PlayerInfo,
                               kcsapi.PlayerResources],
            # Fleets (deck).
            '/api_get_member/deck': [kcsapi.ShipList,  # For away_for_mission
                                     kcsapi.FleetList,
                                     kcsapi.MissionList],
            '/api_req_hensei/change': [kcsapi.FleetList],
            # Equipments (slot items).
            # unsetslot holds the order of equipment items per type. This must
            # be handled after slot_item. Currently the client seem to call it
            # in the proper order but it could change in the future.
            '/api_get_member/slot_item': [kcsapi.EquipmentList],
            '/api_get_member/unsetslot': [kcsapi.EquipmentList],
            '/api_req_kaisou/lock': [kcsapi.EquipmentList],
            '/api_req_kaisou/slotset': [kcsapi.EquipmentList],
            '/api_req_kaisou/unsetslot_all': [kcsapi.EquipmentList],
            # Rebuilding.
            '/api_req_kaisou/remodeling': [kcsapi.ShipList],
            '/api_req_kaisou/powerup': [kcsapi.ShipList],
            # Repair docks.
            '/api_get_member/ndock': [kcsapi.RepairDock,
                                      kcsapi.ShipList],
            '/api_req_nyukyo/speedchange': [kcsapi.RepairDock,
                                            kcsapi.ShipList],
            '/api_req_nyukyo/start': [kcsapi.RepairDock,
                                      kcsapi.ShipList],
            # Shipyard and build docks.
            # destroyship must handle EquipmentList before ShipList to get the
            # list of equipments to be disposed.
            '/api_get_member/kdock': [kcsapi.BuildDock],
            '/api_req_kousyou/createship': [kcsapi.NullHandler()],
            '/api_req_kousyou/createship_speedchange': [kcsapi.BuildDock],
            '/api_req_kousyou/createitem': [kcsapi.EquipmentList],
            '/api_req_kousyou/destroyitem2': [kcsapi.PlayerResources,
                                              kcsapi.EquipmentList],
            '/api_req_kousyou/destroyship': [kcsapi.PlayerResources,
                                             kcsapi.EquipmentList,
                                             kcsapi.ShipList],
            '/api_req_kousyou/getship': [kcsapi.ShipList,
                                         kcsapi.BuildDock,
                                         kcsapi.EquipmentList],
            # Quests.
            '/api_get_member/questlist': [kcsapi.QuestList],
            '/api_req_quest/start': [kcsapi.NullHandler()],
            '/api_req_quest/stop': [kcsapi.NullHandler()],
            # Expedition.
            '/api_get_member/mapcell': [kcsapi.NullHandler()],
            '/api_get_member/mapinfo': [kcsapi.NullHandler()],
            '/api_req_combined_battle/battle': [kcsapi.Battle,
                                                kcsapi.ShipList],
            '/api_req_combined_battle/battleresult': [kcsapi.ExpeditionResult],
            '/api_req_combined_battle/battle_water': [kcsapi.Battle,
                                                      kcsapi.ShipList],
            '/api_req_combined_battle/midnight_battle': [kcsapi.MidnightBattle,
                                                         kcsapi.ShipList],
            '/api_req_battle_midnight/battle': [kcsapi.MidnightBattle,
                                                kcsapi.ShipList],
            '/api_req_battle_midnight/sp_midnight': [kcsapi.MidnightBattle,
                                                     kcsapi.ShipList],
            '/api_req_map/start': [kcsapi.Expedition],
            '/api_req_map/next': [kcsapi.Expedition],
            '/api_req_sortie/battle': [kcsapi.Battle,
                                       kcsapi.ShipList],
            '/api_req_sortie/battleresult':
            [kcsapi.ExpeditionResult],
            # Practice.
            '/api_get_member/practice': [kcsapi.PracticeList],
            '/api_req_member/get_practice_enemyinfo':
            [kcsapi.PracticeList],
            '/api_req_practice/battle': [kcsapi.PracticeList,
                                         kcsapi.Battle,
                                         kcsapi.ShipList],
            '/api_req_practice/battle_result': [kcsapi.PracticeList],
            '/api_req_practice/midnight_battle': [kcsapi.MidnightBattle,
                                                  kcsapi.ShipList],
            # Missions.
            '/api_get_member/mission': [kcsapi.MissionList],
            '/api_req_mission/start': [kcsapi.ShipList,
                                       kcsapi.FleetList,
                                       kcsapi.MissionList],
            '/api_req_mission/result': [kcsapi.NullHandler()],
            # Items.
            #'/api_get_member/useitem': [],
            # Furnitures.
            '/api_get_member/furniture': [kcsapi.NullHandler()],
        }
        # Eager handlers accept all KCSAPI responses regardless of API URL.
        self.kcsapi_eager_handlers = [
            kcsapi.Screen,
        ]

    def define_requestables(self):
        self.requestables = {
            'SavedFleetDeploymentShipIdList':
            kcsapi.SavedFleetDeploymentShipIdList(),
            'FleetDeploymentShipIdList': kcsapi.FleetDeploymentShipIdList(),
            'CombinedFleetDeploymentShipIdList':
            kcsapi.CombinedFleetDeploymentShipIdList(),
        }

    def define_journals(self):
        self.journals = {
            'PlayerResourcesJournal': kcsapi.PlayerResourcesJournal,
        }

    def load_journals(self, journal_basedir):
        if not journal_basedir:
            self._logger.info('Journal basedir is empty. No journal will be '
                              'saved after the process ends.')
            self.loaded_journals = {name: cls() for name, cls in
                                    self.journals.iteritems()}
            self.requestables.update(self.loaded_journals)
            return
        if not os.path.isdir(journal_basedir):
            os.mkdir(journal_basedir)
        self.loaded_journals = {}
        for name, cls in self.journals.iteritems():
            filename = os.path.join(journal_basedir, name)
            if journal_basedir and os.path.isfile(filename):
                self._logger.info('Loading journal {} from {}'.format(
                    name, filename))
                with open(filename, 'r') as journal_file:
                    journal = cls.parse_text(journal_file.read())
                    journal.clean_up_old_entries()
                    self.loaded_journals[name] = journal
            else:
                self._logger.info('Creating a new journal {}'.format(name))
                self.loaded_journals[name] = cls()
        self.requestables.update(self.loaded_journals)

    def save_journals(self, journal_basedir):
        if not journal_basedir:
            return
        for name, journal in self.loaded_journals.iteritems():
            num_entries = journal.clean_up_old_entries()
            if num_entries == 0:
                self._logger.info(
                    'Found 0 entries in journal {}. Looks like a bug and the '
                    'journal will not be overwritten.'.format(name))
                continue
            filename = os.path.join(journal_basedir, name)
            self._logger.info('Saving journal {} to {}'.format(
                name, filename))
            with open(filename, 'w') as journal_file:
                journal_string = journal.json(
                    indent=2, separators=(',', ': '), sort_keys=True,
                    ensure_ascii=False).encode('utf8')
                journal_file.write(journal_string)

    def serialize_objects(self):
        """Serialize objects so that the client can deserialize and restore the
        state."""
        return {key: [value.__class__.__module__, value.__class__.__name__,
                      value.json()]
                for key, value in self.objects.iteritems()}

    def deserialize_objects(self, serialized_objects):
        """Deserialize objects to restore the previous state.

        *IMPORTANT NOTE: this method uses :meth:`eval` to find the module (the
        first value in the list). Do not call this method with a data from an
        untrusted source.*
        """
        namespace = __name__.rpartition('.')[0]
        namespace = namespace + '.' if namespace else ''
        for key, value in serialized_objects.iteritems():
            module_name, class_name, text = value
            if module_name.startswith(namespace):
                module_name = module_name[len(namespace):]
            module = eval(module_name)
            cls = getattr(module, class_name)
            self.objects[key] = cls.parse_text(text)

    def get_kcsapi_responses(self, entries):
        for entry in entries:
            o = urlparse.urlparse(entry['request']['url'])
            match = KCSAPI_PATH_REGEX.match(o.path)
            if match:
                api_name = match.group('api_name')
                request = kcsapi.jsonobject.parse(
                    {param['name']: param['value'] for param in
                     entry['request']['postData']['params']},
                    readonly=True, omittable=False)
                content = entry['response']['content']
                text = content['text']
                # Highly likely the KCSAPI response is Base64 encoded, because
                # the API server doesn't attach charset information.
                encoding = content.get('encoding')
                if encoding == 'base64':
                    text = base64.b64decode(text)
                # Remove BOM if any.
                if text.startswith(BOM):
                    text = text[len(BOM):]
                # Skip response prefix which makes JSON parsing fail.
                if text.startswith(KCSAPI_PREFIX):
                    text = text[len(KCSAPI_PREFIX):]
                else:
                    self._logger.debug(
                        'Unexpected KCSAPI response got for {}'.format(o.path))
                    self._logger.debug(
                        'Raw response: {}'.format(text))
                    self._logger.debug('First 64 bytes: {}'.format(
                        ' '.join(('{:X}'.format(ord(c))) for c in text[:64])))
                    continue
                # KCSAPI response should be in UTF-8.
                response = kcsapi.jsonobject.parse_text(
                    text, readonly=True, omittable=False, encoding='utf8')
                yield api_name, request, response

    def dispatch(self, api_name, request, response):
        try:
            handlers = self.kcsapi_handlers[api_name]
            self._logger.debug('Accessed KCSAPI: {}'.format(api_name))
        except KeyError:
            handlers = [kcsapi.DefaultHandler(api_name)]
            self._logger.debug('Unknown KCSAPI:  {}'.format(api_name))
        for handler in handlers + self.kcsapi_eager_handlers:
            object_type = handler.__name__
            old_obj = self.objects.get(object_type)
            if not old_obj:
                obj = handler()
                # Handler may return None in case there is no need to handle
                # the KCSAPI response.
                if obj:
                    try:
                        obj.update(api_name, request, response, self.objects,
                                   self.debug)
                        self.objects[object_type] = obj
                        yield obj
                    except:
                        self._logger.error(traceback.format_exc())
                        # In debug mode, update the object anyways to see the
                        # raw transaction in the debug UI. This would deliver
                        # an incomplete data to the client.
                        if self.debug:
                            self.objects[object_type] = obj
                            yield obj
            else:
                try:
                    old_obj.update(api_name, request, response, self.objects,
                                   self.debug)
                    yield old_obj
                except:
                    self._logger.error(traceback.format_exc())
                    if self.debug:
                        yield old_obj

    def get_updated_objects(self):
        entries = self.har_manager.get_updated_entries()
        if not entries:
            return
        api_names = []
        for api_name, request, response in self.get_kcsapi_responses(entries):
            # Process only succeeded ones.
            if not response.api_result:
                self._logger.warn('KCSAPI request on {} failed.'.format(
                    api_name))
                continue
            for obj in self.dispatch(api_name, request, response):
                yield obj
                api_names.append(api_name)
        for journal in self.loaded_journals.itervalues():
            journal._update(api_names, self.objects)

    def request(self, command):
        if len(command) != 2:
            raise ValueError(
                'Command should have the type and args: {}'.format(command))
        command_type, command_args = command
        requestable = self.requestables.get(command_type)
        if requestable:
            try:
                return requestable._request(self.objects, **command_args)
            except TypeError:
                self._logger.error(
                    'Requestable argument mismatch or some type error. '
                    'type = {}, args = {}'
                    .format(command_type, command_args))
                raise
        else:
            raise ValueError('Unknown command type: {}'.format(command_type))

    def update_preferences(self, preferences):
        self.objects['Preferences'] = preferences
        if 'ShipList' in self.objects:
            self.objects['ShipList'].update_tags(preferences.ship_prefs.tags)
