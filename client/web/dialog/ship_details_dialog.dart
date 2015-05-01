import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../component/deployedequipmentlist.dart';
import '../model/assistant.dart';
import '../util.dart';

@CustomTag('kcaa-ship-details-dialog')
class ShipDetailsDialog extends KcaaDialog {

  @observable Ship ship;
  @observable List<String> tags = new ObservableList<String>();
  @observable List<int> loadableEquipmentTypes = new ObservableList<int>();
  @observable List<int> expandedEquipmentTypes = new ObservableList<int>();
  @observable int selectedDefinitionId;
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
    resetLoadableEquipmentTypes();
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
      updateShipTags(model);
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

  void remodel() {
    Uri request = assistant.serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "RemodelShip",
          "ship_id": ship.id.toString(),
        }));
    HttpRequest.getString(request.toString());
  }

  void resetLoadableEquipmentTypes() {
    loadableEquipmentTypes.clear();
    model.shipTypeDefinitionMap[ship.shipTypeId].loadableEquipmentTypes.forEach(
        (equipmentType, loadable) {
      if (loadable) {
        loadableEquipmentTypes.add(equipmentType);
      }
    });
    // Some ships have additional loadable equipment types in addition to the
    // default types defined by the ship.
    for (var type in ship.additionalLoadableEquipmentTypes) {
      loadableEquipmentTypes.add(type);
    }
    loadableEquipmentTypes.sort();
  }

  void resetEquipmentSelectionMode() {
    if (selectedEquipmentRow != null) {
      selectedEquipmentRow.classes.remove("selected");
    }
    selectingEquipment = false;
    selectedSlot = null;
    selectedEquipmentRow = null;
    expandedEquipmentTypes.clear();
    selectedDefinitionId = null;
  }

  void clearEquipments() {
    Uri request = assistant.serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "ClearEquipments",
          "ship_id": ship.id.toString(),
        }));
    HttpRequest.getString(request.toString());
    resetEquipmentSelectionMode();
  }

  void selectNewEquipment(Event e, DeployedEquipmentEventDetail detail, var _) {
    if (selectedEquipmentRow != null) {
      selectedEquipmentRow.classes.remove("selected");
    }
    if (selectingEquipment && detail.slot == selectedSlot) {
      selectingEquipment = false;
      selectedSlot = null;
      return;
    }
    selectingEquipment = true;
    selectedSlot = detail.slot;
    selectedEquipmentRow = detail.target.parent.parent.parent;
    selectedEquipmentRow.classes.add("selected");
    expandedEquipmentTypes.clear();
    var definition = ship.equipments[detail.slot].definition;
    expandedEquipmentTypes.add(definition.type);
    selectedDefinitionId = definition.id;
  }

  void clearEquipment(Event e, DeployedEquipmentEventDetail detail, var _) {
    var equipmentDefinitionIds = new List<int>.generate(
        ship.equipments.length, (_) => EquipmentDefinition.ID_KEEP);
    equipmentDefinitionIds[detail.slot] = EquipmentDefinition.ID_EMPTY;
    requestReplaceEquipments(equipmentDefinitionIds);
  }

  void replaceEquipment(Event e, int equipmentDefinitionId, Element target) {
    var equipmentDefinitionIds = new List<int>.generate(
        ship.equipments.length, (_) => EquipmentDefinition.ID_KEEP);
    equipmentDefinitionIds[selectedSlot] = equipmentDefinitionId;
    requestReplaceEquipments(equipmentDefinitionIds);
  }

  void requestReplaceEquipments(List<int> equipmentDefinitionIds) {
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
