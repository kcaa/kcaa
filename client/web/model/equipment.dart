part of kcaa_model;

class EquipmentDefinition extends Observable {
  @observable int id;
  @observable String name;
  @observable int type;
  @observable String typeName;
  @observable String description;
  @observable int firepower, fireHit, fireFlee;
  @observable int thunderstroke, torpedoHit;
  @observable int antiAir;
  @observable int armor;
  @observable int antiSubmarine;
  @observable int bombPower;
  @observable int scouting;
  @observable int firingRange;
  @observable int rarity;
  @observable int sortOrder;
  @observable final List<Equipment> instances = new ObservableList<Equipment>();

  void update(Map<String, dynamic> data) {
    id = data["id"];
    name = data["name"];
    type = data["type"];
    typeName = data["type_name"];
    description = data["description"];
    firepower = data["firepower"];
    fireHit = data["fire_hit"];
    fireFlee = data["fire_flee"];
    thunderstroke = data["thunderstroke"];
    torpedoHit = data["torpedo_hit"];
    antiAir = data["anti_air"];
    armor = data["armor"];
    antiSubmarine = data["anti_submarine"];
    bombPower = data["bomb_power"];
    scouting = data["scouting"];
    firingRange = data["firing_range"];
    rarity = data["rarity"];
    sortOrder = data["sort_order"];
  }
}

class Equipment extends Observable {
  @observable int id;
  @observable EquipmentDefinition definition;
  @observable int level;
  @observable bool locked;

  void update(Map<String, dynamic> data,
              Map<int, EquipmentDefinition> definitionMap) {
    id = data["id"];
    definition = definitionMap[data["item_id"]];
    level = data["level"];
    locked = data["locked"];
  }
}

void handleEquipmentDefinitionList(Assistant assistant, AssistantModel model,
                                   Map<String, dynamic> data) {
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
}

void handleEquipmentList(Assistant assistant, AssistantModel model,
                         Map<String, dynamic> data) {
  model.numEquipments = 0;
  for (var definition in model.equipmentDefinitions) {
    definition.instances.clear();
  }
  for (var equipmentData in (data["items"] as Map).values) {
    Equipment equipment = new Equipment();
    equipment.update(equipmentData, model.equipmentDefinitionMap);
    equipment.definition.instances.add(equipment);
    model.numEquipments += 1;
  }
}