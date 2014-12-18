import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';

class InstanceGroup extends Observable {
  @observable Ship ship;
  @observable int level;
  @observable bool locked;
  List<Equipment> instances = new List();

  InstanceGroup(this.ship, this.level, this.locked);
}

@CustomTag('kcaa-equipment-details-dialog')
class EquipmentDetailsDialog extends KcaaDialog {
  @observable EquipmentDefinition definition;
  @observable final List<InstanceGroup> instanceGroups =
      new ObservableList<InstanceGroup>();

  EquipmentDetailsDialog.created() : super.created();

  @override
  void show(Element target) {
    var definitionId = int.parse(target.dataset["equipmentDefinitionId"]);
    definition = model.equipmentDefinitionMap[definitionId];
    updateInstanceGroups();
  }

  void updateInstanceGroups() {
    definition.instances.sort();
    instanceGroups.clear();
    // Cluster instances into groups.
    Equipment lastInstance = null;
    InstanceGroup group = null;
    for (var instance in definition.instances) {
      print("id: ${instance.id}, level: ${instance.level}, locked: ${instance.locked}, ship: ${instance.ship != null ? instance.ship.name : ''}");
      if (lastInstance == null || lastInstance.compareTo(instance) != 0) {
        group = new InstanceGroup(instance.ship, instance.level,
            instance.locked);
        group.instances.add(instance);
        instanceGroups.add(group);
      } else {
        group.instances.add(instance);
      }
      lastInstance = instance;
    }
  }

  void ok() {
    close();
  }
}