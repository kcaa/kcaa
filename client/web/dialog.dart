library kcaa_dialog;

import 'dart:html';
import 'package:polymer/polymer.dart';
import 'package:intl/intl.dart';

import 'assistant.dart';
import 'model/assistant.dart';

class KcaaDialog extends PolymerElement {
  // Model and the assistant element. These values are set during the
  // initialization phase of the assistant element.
  @observable AssistantModel model;
  Assistant assistant;

  KcaaDialog.created() : super.created();

  // Called when the dialog is being shown.
  void show(Element target) {}

  @observable
  void close() {
    querySelector("#modalDialogContainer").classes.remove("in");
    this.classes.add("hidden");
  }
}

class FriendlyScheduleFragment extends Observable {
  @observable String start;
  @observable String end;

  FriendlyScheduleFragment.empty() {
    start = "0:00";
    end = "0:00";
  }

  FriendlyScheduleFragment(ScheduleFragment fragment) {
    var startHour = fragment.start ~/ 3600;
    var startMin = (fragment.start - 3600 * startHour) ~/ 60;
    var startMinPadding = startMin < 10 ? "0" : "";
    start = "${startHour}:${startMinPadding}${startMin}";
    var endHour = fragment.end ~/ 3600;
    var endMin = (fragment.end - 3600 * endHour) ~/ 60;
    var endMinPadding = endMin < 10 ? "0" : "";
    end = "${endHour}:${endMinPadding}${endMin}";
  }

  ScheduleFragment toScheduleFragment() {
    var startComponents = start.split(":");
    var endComponents = end.split(":");
    if (startComponents.length != 2 || endComponents.length != 2) {
      throw new FormatException("Schedule fragments must have 2 components");
    }
    var startHour = int.parse(startComponents[0]);
    var startMin = int.parse(startComponents[1]);
    var endHour = int.parse(endComponents[0]);
    var endMin = int.parse(endComponents[1]);
    if (startHour < 0 || startMin < 0 || startMin >= 60 ||
        endHour < 0 || endMin < 0 || endMin >= 60) {
      throw new FormatException("Invalid range for hour:minute components");
    }
    return new ScheduleFragment(3600 * startHour + 60 * startMin,
        3600 * endHour + 60 * endMin);
  }
}

@CustomTag('kcaa-schedule-dialog')
class ScheduleDialog extends KcaaDialog {
  @observable bool enabled;
  @observable List<FriendlyScheduleFragment> schedules =
      new ObservableList();
  @observable String errorMessage;

  ScheduleDialog.created() : super.created();

  @override
  void show(Element target) {
    enabled = model.autoManipulatorsEnabled;
    schedules.clear();
    schedules.addAll(model.autoManipulatorSchedules.map(
        (fragment) => new FriendlyScheduleFragment(fragment)));
    errorMessage = null;
  }

  void addSchedule() {
    schedules.add(new FriendlyScheduleFragment.empty());
  }

  void removeSchedule(MouseEvent e, var detail, Element target) {
    var index = int.parse(target.dataset["index"]);
    schedules.removeAt(index);
  }

  void validateSchedule(Event e, var detail, Element target) {
    try {
      var dummy = new FriendlyScheduleFragment.empty();
      dummy.start = (target as InputElement).value;
      dummy.toScheduleFragment();
      target.classes.remove("invalid");
    } on FormatException {
      target.classes.add("invalid");
    }
  }

  void ok() {
    try {
      assistant.setAutoManipulatorSchedules(enabled, schedules.map(
          (fragment) => fragment.toScheduleFragment()));
      close();
    } on FormatException {
      errorMessage = "時刻指定に誤りがあります。";
    }
  }
}

class EvaluatedMission extends Observable {
  @observable Mission mission;
  @observable int fuelProfit;
  @observable int ammoProfit;

  EvaluatedMission(Mission mission, Fleet fleet) {
    this.mission = mission;
    var fuelConsumption = fleet.ships
        .map((ship) => ship.fuelCapacity * mission.fuelConsumption / 100)
        .reduce((x, y) => x + y)
        .toInt();
    var ammoConsumption = fleet.ships
        .map((ship) => ship.ammoCapacity * mission.ammoConsumption / 100)
        .reduce((x, y) => x + y)
        .toInt();
    fuelProfit = mission.fuel - fuelConsumption;
    ammoProfit = mission.ammo - ammoConsumption;
  }
}

@CustomTag('kcaa-fleet-mission-dialog')
class FleetMissionDialog extends KcaaDialog {
  @observable Fleet fleet;
  @observable List<EvaluatedMission> evaled_missions;

  FleetMissionDialog.created() : super.created();

  @override
  void show(Element target) {
    var fleetId = int.parse(target.dataset["fleetId"]);
    fleet = model.fleets[fleetId - 1];
    evaled_missions = new ObservableList<EvaluatedMission>.from(model.missions
        .where((mission) => mission.undertakingFleetId == -1)
        .map((mission) => new EvaluatedMission(mission, fleet)));
  }

  void goOnMission(MouseEvent e, var detail, Element target) {
    var fleetId = fleet.id.toString();
    var missionId = target.dataset["missionId"];
    Uri request = assistant.serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "GoOnMission",
          "fleet_id": fleetId,
          "mission_id": missionId,
        }));
    HttpRequest.getString(request.toString());
    close();
  }
}