import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';
import '../util.dart';

@CustomTag('kcaa-fleet-organization-dialog')
class FleetOrganizationDialog extends KcaaDialog {
  @observable SavedFleet fleet;
  @observable List<Ship> ships;

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
    fleet = model.preferences.fleetPrefs.savedFleets.firstWhere(
        (savedFleet) => savedFleet.name == fleetName);
    ships = new ObservableList<Ship>.from(fleet.shipRequirements.map(
        (requirement) => model.shipMap[requirement.id]));
    debug = model.debug;

    editingFleetName = false;
    fleetNameToDelete = "";
    errorMessage = null;
    $["fleetNameToDelete"].classes.remove("invalid");
  }

  void ok() {
    // TODO: Update saved fleet requirements.
    close();
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