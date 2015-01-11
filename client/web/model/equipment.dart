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
  @observable int numAvailable;

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
    numAvailable = 0;  // updated by updateAvailableEquipments()
  }
}

class Equipment extends Observable implements Comparable<Equipment> {
  // ID meaning the slow should be empty.
  static final int EQUIPMENT_ID_EMPTY = -1;
  // ID meaning the slot should be kept intact.
  static final int EQUIPMENT_ID_KEEP = -2;

  @observable int id;
  @observable EquipmentDefinition definition;
  @observable int level;
  @observable bool locked;
  @observable Ship ship;

  void update(Map<String, dynamic> data,
              Map<int, EquipmentDefinition> definitionMap) {
    id = data["id"];
    definition = definitionMap[data["item_id"]];
    level = data["level"];
    locked = data["locked"];
  }

  int compareTo(Equipment other) {
    // Place non-equipped ones first.
    if (ship == null && other.ship != null) {
      return -1;
    } else if (ship != null && other.ship == null) {
      return 1;
    }
    // If equipping ships are different, prefer one equipped by the ship with
    // higher level.
    if (ship != null && other.ship != null) {
      var shipComparison = Ship.compareByKancolleLevel(ship, other.ship);
      if (shipComparison != 0) {
        return -shipComparison;
      }
    }
    // Otherwise prefer a locked, higher level one.
    if (locked != other.locked) {
      return locked ? -1 : 1;
    }
    if (level != other.level) {
      return -level.compareTo(other.level);
    }
    return 0;
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
  model.equipmentList.update();
}

void handleEquipmentList(Assistant assistant, AssistantModel model,
                         Map<String, dynamic> data) {
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
  emptyDefinition.id = Equipment.EQUIPMENT_ID_EMPTY;
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