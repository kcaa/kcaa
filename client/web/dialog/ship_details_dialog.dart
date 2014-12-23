import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';
import '../util.dart';

@CustomTag('kcaa-ship-details-dialog')
class ShipDetailsDialog extends KcaaDialog {
  @observable Ship ship;
  @observable List<String> tags = new ObservableList<String>();
  @observable bool selectingEquipment;
  int selectedSlot;
  Element selectedEquipmentRow;

  ShipDetailsDialog.created() : super.created();

  @override
  void show(Element target) {
    var shipId = int.parse(target.dataset["shipId"]);
    ship = model.shipMap[shipId];
    tags.clear();
    tags.addAll(ship.tags);
    resetEquipmentSelectionMode();
  }

  void deleteTag(Event e, var detail, Element target) {
    tags.removeAt(int.parse(target.dataset["index"]));
  }

  void addNewTag(Event e, var detail, InputElement target) {
    tags.add(target.value);
    target.value = "";
  }

  void ok() {
    ShipPrefs shipPrefs = model.preferences.shipPrefs;
    bool prefsChanged = false;
    if (tags.isEmpty) {
      if (shipPrefs.tags.containsKey(ship.id)) {
        shipPrefs.tags.remove(ship.id);
        prefsChanged = true;
      }
    } else {
      if (shipPrefs.tags[ship.id] == null ||
          !iterableEquals(ship.tags, tags)) {
        shipPrefs.tags[ship.id] = new ShipTags(tags);
        prefsChanged = true;
      }
    }
    if (prefsChanged) {
      ship.tags.clear();
      ship.tags.addAll(tags);
      assistant.savePreferences();
    }
    close();
  }

  void placeAsFlagship() {
    Uri request = assistant.serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "LoadShips",
          "fleet_id": "1",
          "ship_ids": ship.id.toString(),
        }));
    HttpRequest.getString(request.toString());
  }

  void resetEquipmentSelectionMode() {
    if (selectedEquipmentRow != null) {
      selectedEquipmentRow.classes.remove("selected");
    }
    selectingEquipment = false;
    selectedSlot = null;
    selectedEquipmentRow = null;
  }

  void selectNewEquipment(Event e, var detail, AnchorElement target) {
    e.preventDefault();
    if (selectedEquipmentRow != null) {
      selectedEquipmentRow.classes.remove("selected");
    }
    var slot = int.parse(target.dataset["slot"]);
    if (selectingEquipment && slot == selectedSlot) {
      selectingEquipment = false;
      selectedSlot = null;
      return;
    }
    selectingEquipment = true;
    selectedSlot = slot;
    selectedEquipmentRow = target.parent.parent.parent;
    selectedEquipmentRow.classes.add("selected");
  }

  void replaceEquipment(Event e, int equipmentDefinitionId, Element target) {
    var equipmentDefinitionIds = new List<int>.from(
        ship.equipments.map((e) => e.definition.id));
    equipmentDefinitionIds[selectedSlot] = equipmentDefinitionId;
    Uri request = assistant.serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "ReplaceEquipments",
          "ship_id": ship.id.toString(),
          "equipment_definition_ids": equipmentDefinitionIds.join(","),
        }));
    HttpRequest.getString(request.toString());
    resetEquipmentSelectionMode();
  }
}