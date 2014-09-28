import 'dart:convert';
import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';

@CustomTag('kcaa-fleet-organization-dialog')
class FleetOrganizationDialog extends KcaaDialog {
  @observable FleetDeployment fleet;
  @observable final List<Ship> ships = new ObservableList<Ship>();

  @observable final String defaultClass = "";
  @observable final bool ignoreFilter = true;
  @observable bool debug = false;

  @observable bool editingFleetName;
  @observable String newFleetName;
  @observable String fleetNameToDelete;
  @observable String errorMessage;

  FleetOrganizationDialog.created() : super.created();

  @override
  void show(Element target) {
    var fleetName = target.dataset["fleetName"];
    // Be sure to create a clone.
    fleet = model.preferences.fleetPrefs.savedFleets.firstWhere(
        (savedFleet) => savedFleet.name == fleetName);
/*    fleet = new FleetDeployment.fromJSON(
        model.preferences.fleetPrefs.savedFleets.firstWhere(
            (savedFleet) => savedFleet.name == fleetName).toJSONEncodable());*/
    ships.clear();
    assistant.requestObject("SavedFleetDeploymentShipIdList",
        {"fleet_name": fleetName}).then((Map<String, dynamic> data) {
      for (var shipId in data["ship_ids"]) {
        ships.add(model.shipMap[shipId]);
      }
    });
    debug = model.debug;

    editingFleetName = false;
    fleetNameToDelete = "";
    errorMessage = null;
    $["fleetNameToDelete"].classes.remove("invalid");
  }

  void editFleetName() {
    editingFleetName = true;
    newFleetName = fleet.name;
  }

  void renameFleet() {
    if (newFleetName == fleet.name) {
      editingFleetName = false;
      return;
    }
    if (model.preferences.fleetPrefs.savedFleets.any((savedFleet) =>
        savedFleet != fleet && savedFleet.name == newFleetName)) {
      errorMessage = "既に同じ名前の艦隊があります。";
      return;
    }
    for (var practicePlan in model.preferences.practicePrefs.practicePlans) {
      if (practicePlan.fleetName == fleet.name) {
        practicePlan.fleetName = newFleetName;
      }
    }
    for (var missionPlan in model.preferences.missionPrefs.missionPlans) {
      if (missionPlan.fleetName == fleet.name) {
        missionPlan.fleetName = newFleetName;
      }
    }
    fleet.name = newFleetName;
    assistant.savePreferences();
    editingFleetName = false;
  }

  void cancelRenaming() {
    editingFleetName = false;
  }

  void loadFleet(MouseEvent e, var detail, Element target) {
    // TODO: Reuse Assistant.loadFleet (probably by moving to util?)
    var fleetId = target.dataset["fleetId"];
    Uri request = assistant.serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "LoadFleet",
          "fleet_id": fleetId,
          "saved_fleet_name": fleet.name,
        }));
    HttpRequest.getString(request.toString());
    close();
  }

  void selectionUpdated(Event e, var detail, SelectElement target) {
    updateExpectation(e, detail, target);
  }

  void updateExpectation(Event e, var detail, Element target) {
    assistant.requestObject("FleetDeploymentShipIdList",
        {"fleet_deployment": JSON.encode(fleet.toJSONEncodable())}).then(
            (Map<String, dynamic> data) {
      ships.clear();
      for (var shipId in data["ship_ids"]) {
        ships.add(model.shipMap[shipId]);
      }
    });
  }

  void delete() {
    if (fleetNameToDelete != fleet.name) {
      errorMessage = "確認のため、削除したい艦隊の名前を正確に入力してください。";
      $["fleetNameToDelete"].classes.add("invalid");
      return;
    }
    if (model.preferences.practicePrefs.practicePlans.any(
        (practicePlan) => practicePlan.fleetName == fleet.name)) {
      errorMessage = "この艦隊は演習計画に組み込まれています。先に計画から外してください。";
      return;
    }
    if (model.preferences.missionPrefs.missionPlans.any(
        (missionPlan) => missionPlan.fleetName == fleet.name)) {
      errorMessage = "この艦隊は遠征計画に組み込まれています。先に計画から外してください。";
      return;
    }
    model.preferences.fleetPrefs.savedFleets.removeWhere(
        (savedFleet) => savedFleet == fleet);
    assistant.savePreferences();
    close();
  }
}