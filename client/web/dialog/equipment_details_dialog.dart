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

  void dismantle(Event e, var detail, Element target) {
    var groupIndex = int.parse(target.dataset["groupIndex"]);
    var group = instanceGroups[groupIndex];
    var ship = group.ship;

    var equipmentDefinitionIds = new List<int>();
    for (var equipment in ship.equipments) {
      var id = EquipmentDefinition.ID_KEEP;
      if (group.instances.contains(equipment)) {
        id = EquipmentDefinition.ID_EMPTY;
      }
      equipmentDefinitionIds.add(id);
    }
    requestReplaceEquipments(ship, equipmentDefinitionIds);
  }

  // TODO: Factor out to the ServerRequests class or somewhere.
  void requestReplaceEquipments(Ship ship, List<int> equipmentDefinitionIds) {
    Uri request = assistant.serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "ReplaceEquipments",
          "ship_id": ship.id.toString(),
          "equipment_definition_ids": equipmentDefinitionIds.join(","),
        }));
    HttpRequest.getString(request.toString());
  }
}