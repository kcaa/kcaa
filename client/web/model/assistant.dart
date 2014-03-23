library kcaa_model;

import 'package:intl/intl.dart';
import 'package:polymer/polymer.dart';

import '../assistant.dart';
import '../util.dart';

part 'questlist.dart';
part 'client.dart';
part 'fleet.dart';
part 'missionlist.dart';
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

  // Missions.
  @observable final List<Mission> missions = new ObservableList<Mission>();

  // Client status.
  @observable String screen;
  @observable String runningManipulator;
  @observable final List<String> manipulatorsInQueue =
      new ObservableList<String>();
  @observable bool autoManipulatorsEnabled = true;
  final List<ScheduleFragment> autoManipulatorSchedules =
      new ObservableList<ScheduleFragment>();
}