part of kcaa_controller;

void handleEquipmentDefinitionList(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  for (var definitionData in (data["items"] as Map).values) {
    var id = definitionData["id"];
    var definition = model.equipmentDefinitionMap[id];
    if (definition == null) {
      definition = new EquipmentDefinition();
      model.equipmentDefinitionMap[id] = definition;
    }
    definition.update(definitionData);
  }
  var definitionsLength = model.equipmentDefinitionMap.length;
  resizeList(model.equipmentDefinitions, definitionsLength,
      () => new EquipmentDefinition());
  var sortedDefinitions =
      model.equipmentDefinitionMap.values.toList(growable: false);
  sortedDefinitions.sort((a, b) {
    if (a.type != b.type) {
      return a.type.compareTo(b.type);
    }
    return a.id.compareTo(b.id);
  });
  for (var i = 0; i < definitionsLength; i++) {
    var definition = sortedDefinitions[i];
    if (model.equipmentDefinitions[i] != definition) {
      model.equipmentDefinitions[i] = definition;
    }
  }
  assistant.equipmentList.update();
}

void handleEquipmentList(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  model.numEquipments = 0;
  var newMap = new Map<int, Equipment>();
  for (var definition in model.equipmentDefinitions) {
    definition.instances.clear();
  }
  for (var equipmentData in (data["items"] as Map).values) {
    Equipment equipment = model.equipmentMap[equipmentData["id"]];
    if (equipment == null) {
      equipment = new Equipment();
    }
    equipment.update(equipmentData, model.equipmentDefinitionMap);
    newMap[equipment.id] = equipment;
    equipment.definition.instances.add(equipment);
    model.numEquipments += 1;
    // For debugging, uncomment the following and `sort -n`.
    // TODO: Consider exposing this info to UI when debugging is enabled.
    // That may need considerable infra change, which might not be worth it.
    // print(
    //     "${equipment.id}) ${equipment.definition.name} " +
    //     "ship ${equipment.ship != null ? equipment.ship.name : '(None)'}, " +
    //     "level: ${equipment.level}, locked: ${equipment.locked}");
  }
  updateAvailableEquipments(model);
  model.equipmentMap = newMap;
  // Virtual entry representing an empty equipment slot.
  var emptyDefinition = new EquipmentDefinition();
  emptyDefinition.id = EquipmentDefinition.ID_EMPTY;
  emptyDefinition.name = "(なし)";
  emptyDefinition.typeName = "空きスロット";
  var emptySlot = new Equipment();
  emptySlot.definition = emptyDefinition;
  model.equipmentMap[-1] = emptySlot;
}

void updateAvailableEquipments(AssistantModel model) {
  for (var definition in model.equipmentDefinitions) {
    definition.numAvailable =
        definition.instances.where((e) => e.ship == null).length;
  }
}
