import 'dart:convert';
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
  @observable final List<Ship> primaryShips = new ObservableList<Ship>();
  @observable final List<Ship> secondaryShips = new ObservableList<Ship>();
  @observable final List<Ship> escotingShips = new ObservableList<Ship>();
  @observable final List<Ship> supportingShips = new ObservableList<Ship>();
  @observable bool loadable = false;

  @observable bool editingFleetName;
  @observable String newFleetName;
  @observable String fleetNameToDelete;
  @observable String errorMessage;

  CombinedFleetOrganizationDialog.created() : super.created();

  // TODO: Consider refactoring with fleet_organization_dialog.dart.
  Ship getShip(int shipId) {
    var ship = model.shipMap[shipId];
    if (ship == null) {
      ship = new Ship();
      if (shipId == 0) {
        ship.name = "該当なし(省略可)";
        ship.stateClass = "dangerous";
      } else {
        ship.name = "該当なし(省略不可)";
        ship.stateClass = "fatal";
      }
    }
    return ship;
  }

  @override
  void show(Element target) {
    primaryShips.clear();
    secondaryShips.clear();
    escotingShips.clear();
    supportingShips.clear();

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
    update(true);
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
    updateExpectation();
  }

  void initFromScratch() {
    fleetIndexInPrefs = null;
    var defaultFleet = primaryFleet.candidates[0].id;
    fleet = new CombinedFleetDeployment("新規連合艦隊編成", defaultFleet, null,
        null, null);
    updateExpectation();
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

  void updateExpectation() {
    update(false);
    var fleetDeployment = JSON.encode(fleet.toJSONEncodable());
    assistant.requestObject("CombinedFleetDeploymentShipIdList",
        {"combined_fleet_deployment": fleetDeployment}).then(
            (Map<String, dynamic> data) {
      primaryShips.clear();
      for (var shipId in data["primary_ship_ids"]) {
        primaryShips.add(getShip(shipId));
      }
      secondaryShips.clear();
      if (fleet.secondaryFleetName != null) {
        for (var shipId in data["secondary_ship_ids"]) {
          secondaryShips.add(getShip(shipId));
        }
      }
      escotingShips.clear();
      if (fleet.escotingFleetName != null) {
        for (var shipId in data["escoting_ship_ids"]) {
          escotingShips.add(getShip(shipId));
        }
      }
      supportingShips.clear();
      if (fleet.supportingFleetName != null) {
        for (var shipId in data["supporting_ship_ids"]) {
          supportingShips.add(getShip(shipId));
        }
      }
      loadable = data["loadable"];
    });
  }

  void update(bool save) {
    fleet.combinedFleetType = int.parse(combinedFleetType.value);
    fleet.primaryFleetName = primaryFleet.value;
    fleet.secondaryFleetName =
        fleet.combinedFleetType == 0 ? null : secondaryFleet.value;
    fleet.escotingFleetName =
        escotingFleetEnabled ? escotingFleet.value : null;
    fleet.supportingFleetName =
        supportingFleetEnabled ? supportingFleet.value : null;

    if (!save) {
      return;
    }
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
    update(true);
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