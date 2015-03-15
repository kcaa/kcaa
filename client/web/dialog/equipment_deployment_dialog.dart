import 'dart:convert';
import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';

class EquipmentDeploymentExpectation extends Observable {
  @observable bool possible;
  @observable Ship ship;
  @observable final ObservableList<Equipment> equipments =
      new ObservableList<Equipment>();

  EquipmentDeploymentExpectation(this.possible, this.ship,
                                 Iterable<Equipment> equipments) {
    this.equipments.addAll(equipments);
  }
}

@CustomTag('kcaa-equipment-deployment-dialog')
class EquipmentDeploymentDialog extends KcaaPaperDialog {
  @published String deployment;

  @observable EquipmentGeneralDeployment generalDeployment;
  int deploymentIndexInPrefs;
  @observable final List<EquipmentDeploymentExpectation> expectations =
      new ObservableList<EquipmentDeploymentExpectation>();

  @observable int tabPage = 0;

  @observable bool editingDeploymentName;
  @observable String newDeploymentName;
  @observable String deploymentNameToDelete;
  @observable String errorMessage;

  EquipmentDeploymentDialog.created() : super.created();
  factory EquipmentDeploymentDialog() =>
      new Element.tag("kcaa-equipment-deployment-dialog");

  // TODO: Merge with FleetOrganizationDialog.
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

  Equipment getEquipment(int equipmentId) {
    var equipment = model.equipmentMap[equipmentId];
    if (equipment == null) {
      equipment = new Equipment();
      equipment.definition = new EquipmentDefinition();
      if (equipmentId == 0) {
        equipment.definition.name = "該当なし(省略可)";
      } else {
        equipment.definition.name = "該当なし(省略不可)";
      }
    }
    return equipment;
  }

  @override
  void initialize() {
    expectations.clear();
    if (deployment != null) {
      initFromName(deployment);
    } else {
      initFromScratch();
    }

    editingDeploymentName = false;
    deploymentNameToDelete = "";
    errorMessage = null;
    $["deploymentNameToDelete"].classes.remove("invalid");
  }

  @override
  void close() {
    if (deploymentIndexInPrefs == null) {
      errorMessage =
          "新しい装備構成が保存されていません。破棄する場合は削除ボタンを押してください。";
    } else {
      super.close();
      // Hack to avoid an incomplete initialization on KSelection.
      // See fleet_organization_dialog.dart for details. This is just kept not to
      // introduce a similar issue unexpectedly.
      generalDeployment = null;
    }
  }

  void initFromName(String deploymentName) {
    // Be sure to create a clone.
    var deploymentInPrefs = model.preferences.equipmentPrefs.deployments
        .firstWhere((deployment) => deployment.name == deploymentName);
    deploymentIndexInPrefs =
        model.preferences.equipmentPrefs.deployments.indexOf(deploymentInPrefs);
    generalDeployment = new EquipmentGeneralDeployment.fromJSON(
        deploymentInPrefs.toJSONEncodable());
    updateExpectationSafe();
  }

  void initFromScratch() {
    generalDeployment = new EquipmentGeneralDeployment("新規装備構成");
    deploymentIndexInPrefs = null;
  }

  void editDeploymentName() {
    editingDeploymentName = true;
    newDeploymentName = generalDeployment.name;
  }

  void renameDeployment() {
    if (newDeploymentName == generalDeployment.name) {
      editingDeploymentName = false;
      return;
    }
    if (model.preferences.equipmentPrefs.deployments.any((deployment) =>
        deployment != generalDeployment &&
        deployment.name == newDeploymentName)) {
      errorMessage = "既に同じ名前の装備構成があります。";
      return;
    }
    // TODO: Update existing fleet organizations that use this deployment.
    generalDeployment.name = newDeploymentName;
    if (deploymentIndexInPrefs != null) {
      model.preferences.equipmentPrefs.deployments[deploymentIndexInPrefs] =
          generalDeployment;
      assistant.savePreferences();
    }
    editingDeploymentName = false;
  }

  void cancelRenaming() {
    editingDeploymentName = false;
  }

  void updateExpectationSafe() {
    updateExpectation(null, null, new DivElement());
  }

  void updateExpectation(Event e, var detail, Element target) {
    try {
      var deployment = JSON.encode(generalDeployment.toJSONEncodable());
      target.classes.remove("invalid");
      assistant.requestObject("EquipmentGeneralDeploymentExpectation",
          {"general_deployment": deployment}).then(
              (Map<String, dynamic> data) {
        expectations.clear();
        for (var expectation in data["expectations"]) {
          expectations.add(new EquipmentDeploymentExpectation(
              expectation["possible"],
              getShip(expectation["ship_id"]),
              (expectation["equipment_ids"] as Iterable).map((equipmentId) =>
                  getEquipment(equipmentId))));
          // Not sure if this is the best solution, but resizeHandler() will
          // recompute the dialog size.
          dialog.resizeHandler();
        }
      });
    } catch (FormatException) {
      target.classes.add("invalid");
      return;
    }
  }

  void update() {
    if (deploymentIndexInPrefs != null) {
      model.preferences.equipmentPrefs.deployments[deploymentIndexInPrefs] =
          generalDeployment;
    } else {
      deploymentIndexInPrefs =
          model.preferences.equipmentPrefs.deployments.length;
      model.preferences.equipmentPrefs.deployments.add(generalDeployment);
    }
    assistant.savePreferences();
  }

  void updateAndClose() {
    update();
    close();
  }

  void duplicate() {
    var deploymentName = generalDeployment.name;
    var trial = 2;
    while (model.preferences.equipmentPrefs.deployments.any((deployment) =>
        deployment.name == deploymentName)) {
      deploymentName = "${generalDeployment.name}${trial}";
      trial += 1;
    }
    generalDeployment.name = deploymentName;
    deploymentIndexInPrefs = null;
    update();
  }

  void delete() {
    if (deploymentIndexInPrefs == null) {
      deploymentIndexInPrefs = -1;
      close();
      return;
    }
    if (deploymentNameToDelete != generalDeployment.name) {
      errorMessage = "確認のため、削除したい装備構成の名前を正確に入力してください。";
      $["deploymentNameToDelete"].classes.add("invalid");
      return;
    }
    // TODO: Warn if this deployment is used in some fleet organization.
    model.preferences.equipmentPrefs.deployments.removeAt(
        deploymentIndexInPrefs);
    assistant.savePreferences();
    close();
  }

  void addNewDeployment() {
    generalDeployment.deployments.add(new EquipmentDeployment());
    updateExpectationSafe();
  }

  void deleteDeployment(Event e, var detail, Element target) {
    var deploymentIndex = int.parse(target.dataset["deploymentIndex"]);
    generalDeployment.deployments.removeAt(deploymentIndex);
    updateExpectationSafe();
  }

  void addNewRequirement(Event e, var detail, Element target) {
    var deploymentIndex = int.parse(target.dataset["deploymentIndex"]);
    generalDeployment.deployments[deploymentIndex].requirements.add(
        new EquipmentRequirement.any());
    updateExpectationSafe();
  }

  void deleteRequirement(Event e, var detail, Element target) {
    var deploymentIndex = int.parse(target.dataset["deploymentIndex"]);
    var requirementIndex = int.parse(target.dataset["requirementIndex"]);
    generalDeployment.deployments[deploymentIndex].requirements.removeAt(
        requirementIndex);
    updateExpectationSafe();
  }
}