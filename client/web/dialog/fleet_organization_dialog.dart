import 'dart:convert';
import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';
import '../util.dart';

@CustomTag('kcaa-fleet-organization-dialog')
class FleetOrganizationDialog extends KcaaPaperDialog {
  @published String fleetname;
  @published int fleetid;

  @observable FleetDeployment fleet;
  int fleetIndexInPrefs;
  @observable final List<Ship> ships = new ObservableList<Ship>();

  @observable int tabPage = 0;

  @observable bool editingFleetName;
  @observable String newFleetName;
  @observable String fleetNameToDelete;
  @observable String errorMessage;

  FleetOrganizationDialog.created() : super.created();

  Ship getShip(int shipId) {
    var ship = model.shipMap[shipId];
    if (ship == null) {
      ship = new Ship();
      if (shipId == 0) {
        ship.id = 0;
        ship.name = "該当なし(省略可)";
        ship.stateClass = "dangerous";
      } else {
        ship.id = -1;
        ship.name = "該当なし(省略不可)";
        ship.stateClass = "fatal";
      }
    }
    return ship;
  }

  @override
  void initialize() {
    ships.clear();
    if (fleetname != null) {
      initFromFleetName(fleetname);
    } else {
      initFromFleetId(fleetid);
    }
    updateEquipmentDeployments();

    tabPage = 0;
    editingFleetName = false;
    fleetNameToDelete = "";
    errorMessage = null;
    $["fleetNameToDelete"].classes.remove("invalid");
  }

  @override
  void close() {
    if (fleetIndexInPrefs == null) {
      errorMessage =
          "新しい艦隊編成が保存されていません。破棄する場合は削除ボタンを押してください。";
    } else {
      super.close();
      // Hack to avoid an incomplete initialization on fleet.globalPredicate; if
      // the fleet is kept intact and the next fleet is set with the same
      // globalPredicate.type, the select element item is reset to "TRUE" (the
      // first item) even though globalPredicate.type.value is correctly set.
      // Do not do this reset in show(). It's important to have a cycle between
      // this reset and the next set on fleet.
      fleet = null;
    }
  }

  void initFromFleetName(String fleetName) {
    // Be sure to create a clone.
    var fleetInPrefs = model.preferences.fleetPrefs.savedFleets.firstWhere(
        (savedFleet) => savedFleet.name == fleetName);
    fleetIndexInPrefs =
        model.preferences.fleetPrefs.savedFleets.indexOf(fleetInPrefs);
    fleet = new FleetDeployment.fromJSON(fleetInPrefs.toJSONEncodable());
    updateExpectationSafe();
  }

  void initFromFleetId(int fleetId) {
    Fleet fleetToSave = model.fleets[fleetId - 1];
    var fleetName = fleetToSave.name;
    var trial = 2;
    while (model.preferences.fleetPrefs.savedFleets.any((savedFleet) =>
        savedFleet.name == fleetName)) {
      fleetName = "${fleetToSave.name}${trial}";
      trial += 1;
    }
    fleet = new FleetDeployment.fromShips(fleetName, fleetToSave.ships);
    fleetIndexInPrefs = null;
    var dummy = new DivElement();
    updateExpectationSafe();
  }

  void updateEquipmentDeployments() {
    var deployments = model.preferences.equipmentPrefs.deployments.map(
        (deployment) => [deployment.name, deployment.name]);
    for (var requirement in fleet.shipRequirements) {
      requirement.equipmentDeployment.updateCandidates(deployments);
    }
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
    // TODO: Fix the name in combined fleets.
    fleet.name = newFleetName;
    if (fleetIndexInPrefs != null) {
      model.preferences.fleetPrefs.savedFleets[fleetIndexInPrefs] = fleet;
      assistant.savePreferences();
    }
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

  void updateExpectationSafe() {
    updateExpectation(null, null, new DivElement());
  }

  void updateExpectation(Event e, var detail, Element target) {
    try {
      var fleetDeployment = JSON.encode(fleet.toJSONEncodable());
      target.classes.remove("invalid");
      assistant.requestObject("FleetDeploymentShipIdList",
          {"fleet_deployment": fleetDeployment}).then(
              (Map<String, dynamic> data) {
        ships.clear();
        for (var shipId in data["ship_ids"]) {
          ships.add(getShip(shipId));
        }
        dialog.resizeHandler();
      });
    } catch (FormatException) {
      target.classes.add("invalid");
      return;
    }
  }

  void update() {
    if (fleetIndexInPrefs != null) {
      model.preferences.fleetPrefs.savedFleets[fleetIndexInPrefs] = fleet;
    } else {
      fleetIndexInPrefs = model.preferences.fleetPrefs.savedFleets.length;
      model.preferences.fleetPrefs.savedFleets.add(fleet);
    }
    assistant.savePreferences();
  }

  void duplicate() {
    var fleetName = fleet.name;
    var trial = 2;
    while (model.preferences.fleetPrefs.savedFleets.any((savedFleet) =>
        savedFleet.name == fleetName)) {
      fleetName = "${fleet.name}${trial}";
      trial += 1;
    }
    fleet.name = fleetName;
    fleetIndexInPrefs = null;
    update();
  }

  void delete() {
    if (fleetIndexInPrefs == null) {
      fleetIndexInPrefs = -1;
      close();
      return;
    }
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
    model.preferences.fleetPrefs.savedFleets.removeAt(fleetIndexInPrefs);
    assistant.savePreferences();
    close();
  }
}