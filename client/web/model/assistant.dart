library kcaa_model;

import 'dart:convert';
import 'dart:html';
import 'package:intl/intl.dart';
import 'package:polymer/polymer.dart';

import '../assistant.dart';
import '../component/shiplist.dart';
import '../component/equipmentlist.dart';
import '../util.dart';

part 'quest.dart';
part 'client.dart';
part 'equipment.dart';
part 'fleet.dart';
part 'mission.dart';
part 'player.dart';
part 'practice.dart';
part 'preferences.dart';
part 'repairdock.dart';
part 'ship.dart';
part 'shipyard.dart';

class AssistantModel extends Observable {
  // Player.
  @observable PlayerInfo playerInfo = new PlayerInfo();
  @observable PlayerResources resources = new PlayerResources();

  // Quests.
  @observable int numQuests = 0;
  @observable int numQuestsUndertaken = 0;
  @observable final List<Quest> quests = new ObservableList<Quest>();

  // Ships.
  @observable final List<Ship> ships = new ObservableList<Ship>();
  Map<int, Ship> shipMap = new Map<int, Ship>();
  @observable int numFilteredShips = 0;
  Map<int, Ship> shipDefinitionMap = new Map<int, Ship>();
  Map<int, ShipTypeDefinition> shipTypeDefinitionMap =
      new Map<int, ShipTypeDefinition>();
  @observable final List<String> shipTags = new ObservableList<String>();
  ShipListElement shipList;
  @observable int numDamagedShipsToWarmUp = 0;
  @observable int numShipsToWarmUp = 0;
  @observable int numShipsUnderRepair = 0;
  @observable int numShipsToRepair = 0;

  // Fleets.
  @observable final List<Fleet> fleets = new ObservableList<Fleet>();
  @observable bool someFleetChargeable = false;
  // TODO: Move this to somewhere appropriate. (ExpeditionPlan?)
  @observable KSelection formations = new KSelection.from(
      [["0", "単縦陣"],
       ["1", "複縦陣"],
       ["2", "輪形陣"],
       ["3", "梯形陣"],
       ["4", "単横陣"]]);

  // Equipments.
  @observable int numEquipments = 0;
  @observable final List<EquipmentDefinition> equipmentDefinitions =
      new ObservableList<EquipmentDefinition>();
  Map<int, EquipmentDefinition> equipmentDefinitionMap =
      new Map<int, EquipmentDefinition>();
  Map<int, Equipment> equipmentMap = new Map<int, Equipment>();
  EquipmentListElement equipmentList;

  // Repair dock.
  @observable int numShipsBeingRepaired = 0;
  @observable final List<RepairSlot> repairSlots =
      new ObservableList<RepairSlot>();

  // Shipyard.
  @observable int numShipsBeingBuilt = 0;
  @observable final List<BuildSlot> buildSlots =
      new ObservableList<BuildSlot>();
  @observable String buildFuel = "30";
  @observable String buildAmmo = "30";
  @observable String buildSteel = "30";
  @observable String buildBauxite = "30";
  @observable KSelection buildMaterial = new KSelection.from(
      [["1", "1"],
       ["20", "20"],
       ["100", "100"]]);
  @observable bool grandBuilding = false;
  @observable String developFuel = "10";
  @observable String developAmmo = "10";
  @observable String developSteel = "10";
  @observable String developBauxite = "10";

  // Missions.
  @observable final List<Mission> missions = new ObservableList<Mission>();

  // Practices.
  @observable int numPracticesDone = 0;
  @observable final List<Practice> practices = new ObservableList<Practice>();

  // Client status.
  @observable bool debug = false;
  @observable String screen = Screen.SCREEN_MAP[0];
  @observable String runningManipulator;
  @observable final List<String> manipulatorsInQueue =
      new ObservableList<String>();
  @observable bool autoManipulatorsActive = false;

  // Preferences.
  @observable Preferences preferences = new Preferences();
}

// Compare ships by an arbitrary criteria.
typedef int ShipComparer(Ship a, Ship b);

// May or may not invert ship order.
typedef int ShipOrderInverter(int result);

// Filter a ship by checking the criteria.
typedef bool ShipFilterer(Ship s);

// Resize the list target so that its length is equal to that of reference.
// If target is longer, the elements are removed from the end. If target is
// shorter, new elements are pushed using newValue callback.
void resizeList(List target, int length, dynamic newValue()) {
  if (length < target.length) {
    target.removeRange(length, target.length);
  } else {
    for (var i = target.length; i < length; i++) {
      target.add(newValue());
    }
  }
}

String formatShortTime(DateTime dateTime) {
  var date = new DateTime(dateTime.year, dateTime.month, dateTime.day);
  var now = new DateTime.now();
  var today = new DateTime(now.year, now.month, now.day);
  if (date == today) {
    return new DateFormat.Hm("ja_JP").format(dateTime);
  } else {
    return new DateFormat.MMMd("ja_JP").add_Hm().format(dateTime);
  }
}
