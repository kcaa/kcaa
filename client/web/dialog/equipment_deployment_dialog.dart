import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';

@CustomTag('kcaa-equipment-deployment-dialog')
class EquipmentDeploymentDialog extends KcaaDialog {
  @observable EquipmentGeneralDeployment generalDeployment;
  int deploymentIndexInPrefs;

  @observable bool editingDeploymentName;
  @observable String newDeploymentName;
  @observable String deploymentNameToDelete;
  @observable String errorMessage;

  EquipmentDeploymentDialog.created() : super.created();

  @override
  void show(Element target) {
    var deploymentName = target.dataset["deploymentName"];
    if (deploymentName != null) {
      initFromName(deploymentName);
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
    // TODO: Update the expected deployment.
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

  void updateExpectation(Event e, var detail, Element target) {
    try {
      // TODO: Implement.
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
}