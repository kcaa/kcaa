import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';
import '../util.dart';

// TODO: Consider merging some logic with fleet_organization_dialog.dart.

@CustomTag('kcaa-combined-fleet-organization-dialog')
class CombinedFleetOrganizationDialog extends KcaaDialog {
  @observable CombinedFleetDeployment fleet;
  int fleetIndexInPrefs;
  @observable KSelection primaryFleet = new KSelection();
  @observable KSelection secondaryFleet = new KSelection();
  @observable KSelection combinedFleetType = new KSelection.from(
      [["0", "通常艦隊"],
       ["1", "機動艦隊"],
       ["2", "水上艦隊"]]);
  @observable bool escotingFleetEnabled;
  @observable KSelection escotingFleet = new KSelection();
  @observable bool supportingFleetEnabled;
  @observable KSelection supportingFleet = new KSelection();
//  @observable final List<Ship> ships = new ObservableList<Ship>();

  @observable bool editingFleetName;
  @observable String newFleetName;
  @observable String fleetNameToDelete;
  @observable String errorMessage;

  CombinedFleetOrganizationDialog.created() : super.created();

  @override
  void show(Element target) {
//    ships.clear();

    var fleetNames = model.preferences.fleetPrefs.savedFleets.map(
        (savedFleet) => savedFleet.name).toList();
    <KSelection>[primaryFleet, secondaryFleet, escotingFleet, supportingFleet]
        .forEach((fleet) {
      fleet.updateCandidates(fleetNames);
      fleet.value = fleetNames[0];
    });
    combinedFleetType.value = "0";
    escotingFleetEnabled = false;
    supportingFleetEnabled = false;

    var fleetName = target.dataset["fleetName"];
    if (fleetName != null) {
      initFromFleetName(fleetName);
    } else {
      initFromScratch();
    }

    editingFleetName = false;
    fleetNameToDelete = "";
    errorMessage = null;
    $["fleetNameToDelete"].classes.remove("invalid");
  }

  @override
  void close() {
    super.close();
    fleet = null;
    <KSelection>[primaryFleet, secondaryFleet, escotingFleet, supportingFleet]
            .forEach((fleet) {
      fleet.value = null;
    });
  }

  void ok() {
    update();
    close();
  }

  void initFromFleetName(String fleetName) {
    // Be sure to create a clone.
    var fleetInPrefs = model.preferences.fleetPrefs.savedCombinedFleets
        .firstWhere((savedFleet) => savedFleet.name == fleetName);
    fleetIndexInPrefs =
        model.preferences.fleetPrefs.savedCombinedFleets.indexOf(fleetInPrefs);
    fleet = new CombinedFleetDeployment.fromJSON(
        fleetInPrefs.toJSONEncodable());
    combinedFleetType.value = fleet.combinedFleetType.toString();
    primaryFleet.value = fleet.primaryFleetName;
    if (fleet.secondaryFleetName != null) {
      secondaryFleet.value = fleet.secondaryFleetName;
    }
    if (fleet.escotingFleetName != null) {
      escotingFleetEnabled = true;
      escotingFleet.value = fleet.escotingFleetName;
    }
    if (fleet.supportingFleetName != null) {
      supportingFleetEnabled = true;
      supportingFleet.value = fleet.supportingFleetName;
    }
/*
    assistant.requestObject("SavedFleetDeploymentShipIdList",
        {"fleet_name": fleetName}).then((Map<String, dynamic> data) {
      for (var shipId in data["ship_ids"]) {
        ships.add(getShip(shipId));
      }
    });
*/
  }

  void initFromScratch() {
    fleetIndexInPrefs = null;
    fleet = new CombinedFleetDeployment("新規連合艦隊編成", null, null, null,
        null);
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
    if (model.preferences.fleetPrefs.savedCombinedFleets.any((savedFleet) =>
        savedFleet != fleet && savedFleet.name == newFleetName)) {
      errorMessage = "既に同じ名前の艦隊があります。";
      return;
    }
    fleet.name = newFleetName;
    if (fleetIndexInPrefs != null) {
      model.preferences.fleetPrefs.savedCombinedFleets[fleetIndexInPrefs] =
          fleet;
      assistant.savePreferences();
    }
    editingFleetName = false;
  }

  void cancelRenaming() {
    editingFleetName = false;
  }

  void update() {
    fleet.combinedFleetType = int.parse(combinedFleetType.value);
    fleet.primaryFleetName = primaryFleet.value;
    fleet.secondaryFleetName =
        fleet.combinedFleetType == 0 ? null : secondaryFleet.value;
    fleet.escotingFleetName =
        escotingFleetEnabled ? escotingFleet.value : null;
    fleet.supportingFleetName =
        supportingFleetEnabled ? supportingFleet.value : null;

    if (fleetIndexInPrefs != null) {
      model.preferences.fleetPrefs.savedCombinedFleets[fleetIndexInPrefs] =
          fleet;
    } else {
      fleetIndexInPrefs = model.preferences.fleetPrefs.savedFleets.length;
      model.preferences.fleetPrefs.savedCombinedFleets.add(fleet);
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
    model.preferences.fleetPrefs.savedCombinedFleets.removeAt(
        fleetIndexInPrefs);
    assistant.savePreferences();
    close();
  }
}