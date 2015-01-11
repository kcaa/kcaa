library kcaa_equipmentlist;

import 'dart:html';
import 'package:polymer/polymer.dart';

import '../assistant.dart';
import '../model/assistant.dart';

class EquipmentGroup extends Observable {
  @observable int id;
  @observable String name;
  @observable List<EquipmentDefinition> definitions =
      new ObservableList<EquipmentDefinition>();
  @observable bool hidden = true;

  EquipmentGroup(this.id, this.name);
}

@CustomTag('kcaa-equipmentlist')
class EquipmentListElement extends PolymerElement {
  @published Assistant assistant;
  @published List<EquipmentDefinition> definitions;
  @published List<int> enabledtypes;
  @published List<int> expandedtypes;
  @published int selectedid;
  @observable List<EquipmentGroup> groups =
      new ObservableList<EquipmentGroup>();

  EquipmentListElement.created() : super.created();

  @override
  void attached() {
    update();
  }

  void update() {
    var groupMap = new Map<int, EquipmentGroup>();
    groups.clear();
    for (var definition in definitions) {
      if (groupMap.containsKey(definition.type)) {
        groupMap[definition.type].definitions.add(definition);
      } else {
        if (enabledtypes != null && !enabledtypes.contains(definition.type)) {
          continue;
        }
        var group = new EquipmentGroup(definition.type, definition.typeName);
        if (expandedtypes != null && expandedtypes.contains(definition.type)) {
          group.hidden = false;
        }
        group.definitions.add(definition);
        groupMap[definition.type] = group;
        groups.add(group);
      }
    }
  }

  void toggleCollapseSection(MouseEvent e) {
    var collapseButton = e.target as Element;
    var groupId = int.parse(collapseButton.dataset["group"]);
    var group = groups.firstWhere((g) => g.id == groupId);
    group.hidden = !group.hidden;
    collapseButton.text = group.hidden ? "►" : "▼";
  }

  void clickOnEquipment(MouseEvent e, var detail, Element target) {
    if (assistant != null) {
      assistant.showModalDialogByName("kcaaEquipmentDetailsDialog", target);
    } else {
      var equipmentDefinitionId =
          int.parse(target.dataset["equipmentDefinitionId"]);
      dispatchEvent(
          new CustomEvent("equipmentclick", detail: equipmentDefinitionId));
    }
    e.preventDefault();
  }
}