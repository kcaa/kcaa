library kcaa_equipmentlist;

import 'dart:html';
import 'package:polymer/polymer.dart';

import '../assistant.dart';
import '../model/assistant.dart';

class EquipmentGroup extends Observable {
  @observable String name;
  @observable List<EquipmentDefinition> definitions =
      new ObservableList<EquipmentDefinition>();
  @observable bool hidden = true;

  EquipmentGroup(this.name);
}

@CustomTag('kcaa-equipmentlist')
class EquipmentListElement extends PolymerElement {
  @published Assistant assistant;
  @published List<EquipmentDefinition> definitions;
  @observable List<EquipmentGroup> groups =
      new ObservableList<EquipmentGroup>();

  EquipmentListElement.created() : super.created();

  @override
  void attached() {
    update();
  }

  void update() {
    var groupMap = new Map<String, EquipmentGroup>();
    for (var definition in definitions) {
      if (groupMap.containsKey(definition.typeName)) {
        groupMap[definition.typeName].definitions.add(definition);
      } else {
        var group = new EquipmentGroup(definition.typeName);
        group.definitions.add(definition);
        groupMap[definition.typeName] = group;
        groups.add(group);
      }
    }
  }

  void toggleCollapseSection(MouseEvent e) {
    var collapseButton = e.target as Element;
    var groupName = collapseButton.dataset["group"];
    var group = groups.firstWhere((g) => g.name == groupName);
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