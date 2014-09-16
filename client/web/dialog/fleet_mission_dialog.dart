import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';

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
    e.preventDefault();
    close();
  }
}