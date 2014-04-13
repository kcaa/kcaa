library kcaa_model;

import 'package:intl/intl.dart';
import 'package:polymer/polymer.dart';

import '../assistant.dart';
import '../util.dart';

part 'quest.dart';
part 'client.dart';
part 'fleet.dart';
part 'mission.dart';
part 'repairdock.dart';
part 'ship.dart';

class AssistantModel extends Observable {
  // Quests.
  @observable int numQuests = 0;
  @observable int numQuestsUndertaken = 0;
  @observable final List<Quest> quests = new ObservableList<Quest>();

  // Ships.
  @observable final List<Ship> ships = new ObservableList<Ship>();
  Map<int, Ship> shipMap = new Map<int, Ship>();

  // Fleets.
  @observable final List<Fleet> fleets = new ObservableList<Fleet>();

  // Repair dock.
  @observable int numShipsBeingRepaired = 0;
  @observable final List<RepairSlot> repairSlots =
      new ObservableList<RepairSlot>();

  // Missions.
  @observable final List<Mission> missions = new ObservableList<Mission>();

  // Client status.
  @observable String screen;
  @observable String runningManipulator;
  @observable final List<String> manipulatorsInQueue =
      new ObservableList<String>();
  @observable bool autoManipulatorsEnabled = true;
  @observable bool autoManipulatorsActive = false;
  final List<ScheduleFragment> autoManipulatorSchedules =
      new ObservableList<ScheduleFragment>();
}

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