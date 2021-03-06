part of kcaa_model;

class EquipmentDefinition extends Observable {
  // ID meaning the slot should be empty.
  static final int ID_EMPTY = -1;
  // ID meaning the slot should be kept intact.
  static final int ID_KEEP = -2;

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
    numAvailable = 0; // updated by updateAvailableEquipments()
  }
}

class Equipment extends Observable implements Comparable<Equipment> {
  @observable int id;
  @observable EquipmentDefinition definition;
  @observable int level;
  @observable bool locked;
  @observable Ship ship;

  void update(
      Map<String, dynamic> data, Map<int, EquipmentDefinition> definitionMap) {
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

// TODO: Somehow merge with ShipPropertyFilter.
class EquipmentPropertyFilter extends Observable {
  @observable KSelection property = new KSelection.from([
    ["id", "特定装備"],
    ["item_id", "装備"],
    ["level", "強化レベル"],
    ["locked", "ロック"],
    ["definition.type", "種類"],
    ["definition.armor", "装甲"],
    ["definition.firepower", "火力"],
    ["definition.fire_hit", "命中"],
    ["definition.fire_flee", "回避"],
    ["definition.thunderstroke", "雷撃"],
    ["definition.torpedo_hit", "雷撃命中"],
    ["definition.anti_air", "対空"],
    ["definition.anti_submarine", "対潜"],
    ["definition.bomb_power", "爆装"],
    ["definition.scouting", "索敵"],
    ["definition.firing_range", "射程"],
    ["definition.rarity", "レアリティ"]
  ]);
  @observable String value;
  @observable KSelection operator = new KSelection.from([
    ["0", "="],
    ["1", "!="],
    ["2", "<"],
    ["3", "<="],
    ["4", ">"],
    ["5", ">="]
  ]);
  static bool parseBool(String value) => value == "true";
  static final Map<String, Function> VALUE_PARSER_MAP = <String, Function>{
    "id": int.parse,
    "item_id": int.parse,
    "level": int.parse,
    "locked": parseBool,
    "definition.type": int.parse,
    "definition.armor": int.parse,
    "definition.firepower": int.parse,
    "definition.fire_hit": int.parse,
    "definition.fire_flee": int.parse,
    "definition.thunderstroke": int.parse,
    "definition.torpedo_hit": int.parse,
    "definition.anti_air": int.parse,
    "definition.anti_submarine": int.parse,
    "definition.bomb_power": int.parse,
    "definition.scouting": int.parse,
    "definition.firing_range": int.parse,
    "definition.rarity": int.parse,
  };

  EquipmentPropertyFilter.equipmentId(int id) {
    property.value = "id";
    value = id.toString();
    operator.value = "0";
  }

  EquipmentPropertyFilter.fromJSON(Map<String, dynamic> data) {
    property.value = data["property"];
    value = data["value"].toString();
    operator.value = data["operator"].toString();
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "property": property.value,
      "value": Function.apply(VALUE_PARSER_MAP[property.value], [value]),
      "operator": int.parse(operator.value),
    };
  }
}

// TODO: Merge with ShipTagFilter.
class EquipmentTagFilter extends Observable {
  @observable String tag;
  @observable KSelection operator =
      new KSelection.from([["0", "を含む"], ["1", "を含まない"]]);

  EquipmentTagFilter.contains(this.tag) {
    operator.value = "0";
  }

  EquipmentTagFilter.notContains(this.tag) {
    operator.value = "1";
  }

  EquipmentTagFilter.fromJSON(Map<String, dynamic> data) {
    tag = data["tag"];
    operator.value = data["operator"].toString();
  }

  Map<String, dynamic> toJSONEncodable() {
    return {"tag": tag, "operator": int.parse(operator.value),};
  }
}

class EquipmentFilter {
  EquipmentFilter.fromJSON(Map<String, dynamic> data) {}

  Map<String, dynamic> toJSONEncodable() {
    return null;
  }
}

// TODO: Somehow merge with ShipPredicate.
// Probably with generics. This is so ugly, but OK for now to stimulate the
// development.
class EquipmentPredicate extends Observable {
  @observable KSelection type = new KSelection.from([
    ["true", "TRUE"],
    ["false", "FALSE"],
    ["or", "OR"],
    ["and", "AND"],
    ["not", "NOT"],
    ["propertyFilter", "プロパティフィルタ"],
    ["tagFilter", "タグフィルタ"],
    ["filter", "定義済みフィルタ"]
  ]);
  @observable bool true_ = false;
  @observable bool false_ = false;
  @observable final List<EquipmentPredicate> or =
      new ObservableList<EquipmentPredicate>();
  @observable final List<EquipmentPredicate> and =
      new ObservableList<EquipmentPredicate>();
  @observable EquipmentPredicate not;
  @observable EquipmentPropertyFilter propertyFilter =
      new EquipmentPropertyFilter.equipmentId(0);
  @observable ShipTagFilter tagFilter = new ShipTagFilter.contains("");
  @observable EquipmentFilter filter;

  EquipmentPredicate.fromTRUE() {
    type.value = "true";
    true_ = true;
  }

  EquipmentPredicate.fromFALSE() {
    type.value = "false";
    false_ = true;
  }

  EquipmentPredicate.fromOR(Iterable<EquipmentPredicate> predicates) {
    type.value = "or";
    or.addAll(predicates);
  }

  EquipmentPredicate.fromAND(Iterable<EquipmentPredicate> predicates) {
    type.value = "and";
    and.addAll(predicates);
  }

  EquipmentPredicate.fromNOT(this.not) {
    type.value = "not";
  }

  EquipmentPredicate.fromPropertyFilter(this.propertyFilter) {
    type.value = "propertyFilter";
  }

  EquipmentPredicate.fromTagFilter(this.tagFilter) {
    type.value = "tagFilter";
  }

  EquipmentPredicate.fromFilter(this.filter) {
    type.value = "filter";
  }

  EquipmentPredicate.fromJSON(Map<String, dynamic> data) {
    if (data == null) {
      type.value = "true";
      true_ = true;
      return;
    } else if (data["true"] != null) {
      type.value = "true";
      true_ = true;
    } else if (data["false"] != null) {
      type.value = "false";
      false_ = true;
    } else if (data["or"] != null) {
      type.value = "or";
      for (var orData in data["or"]) {
        or.add(new EquipmentPredicate.fromJSON(orData));
      }
    } else if (data["and"] != null) {
      type.value = "and";
      for (var andData in data["and"]) {
        and.add(new EquipmentPredicate.fromJSON(andData));
      }
    } else if (data["not"] != null) {
      type.value = "not";
      not = new EquipmentPredicate.fromJSON(data["not"]);
    } else if (data["property_filter"] != null) {
      type.value = "propertyFilter";
      propertyFilter =
          new EquipmentPropertyFilter.fromJSON(data["property_filter"]);
    } else if (data["tag_filter"] != null) {
      type.value = "tagFilter";
      tagFilter = new ShipTagFilter.fromJSON(data["tag_filter"]);
    } else if (data["filter"] != null) {
      type.value = "filter";
      filter = new EquipmentFilter.fromJSON(data["filter"]);
    } else {
      type.value = "true";
      true_ = true;
    }
  }

  Map<String, dynamic> toJSONEncodable() {
    if (type.value == "true") {
      return {"true": true};
    } else if (type.value == "false") {
      return {"false": true};
    } else if (type.value == "or") {
      return {
        "or": or.map((predicate) => predicate.toJSONEncodable()).toList()
      };
    } else if (type.value == "and") {
      return {
        "and": and.map((predicate) => predicate.toJSONEncodable()).toList()
      };
    } else if (type.value == "not") {
      return {"not": not.toJSONEncodable()};
    } else if (type.value == "propertyFilter") {
      return {"property_filter": propertyFilter.toJSONEncodable()};
    } else if (type.value == "tagFilter") {
      return {"tag_filter": tagFilter.toJSONEncodable()};
    } else if (type.value == "filter") {
      return {"filter": filter.toJSONEncodable()};
    }
    return {"true": true};
  }
}

// TODO: Somehow merge with ShipSorter.
class EquipmentSorter extends Observable {
  @observable final KSelection name = new KSelection.from(
      [["powerup_score", "強化値スコア"], ["definition", "種類ごとの並び順"]]);
  @observable final KSelection reversed =
      new KSelection.from([["true", "一番高い"], ["false", "一番低い"]]);

  EquipmentSorter(String name, bool reversed) {
    this.name.value = name;
    this.reversed.value = reversed.toString();
  }

  EquipmentSorter.powerupScore(bool reversed) {
    name.value = "powerup_score";
    this.reversed.value = reversed.toString();
  }

  EquipmentSorter.definition(bool reversed) {
    name.value = "definition";
    this.reversed.value = reversed.toString();
  }

  EquipmentSorter.fromJSON(Map<String, dynamic> data) {
    name.value = data["name"];
    reversed.value = data["reversed"].toString();
  }

  Map<String, dynamic> toJSONEncodable() {
    return {"name": name.value, "reversed": reversed.value == "true",};
  }
}

class EquipmentRequirement extends Observable {
  static final int TARGET_SLOT_TOPMOST = 0;
  static final int TARGET_SLOT_LARGEST_AIRCRAFT_CAPACITY = 1;

  @observable KSelection targetSlot =
      new KSelection.from([["0", "一番上"], ["1", "艦載機最多"]]);
  @observable EquipmentPredicate predicate;
  @observable EquipmentSorter sorter;
  @observable bool omittable;

  EquipmentRequirement(
      int targetSlot, this.predicate, this.sorter, this.omittable) {
    this.targetSlot.value = targetSlot.toString();
  }

  EquipmentRequirement.any() {
    targetSlot.value = TARGET_SLOT_TOPMOST.toString();
    predicate = new EquipmentPredicate.fromTRUE();
    sorter = new EquipmentSorter.powerupScore(true);
    omittable = false;
  }

  EquipmentRequirement.fromJSON(Map<String, dynamic> data) {
    targetSlot.value = data["target_slot"].toString();
    predicate = new EquipmentPredicate.fromJSON(data["predicate"]);
    sorter = new EquipmentSorter.fromJSON(data["sorter"]);
    omittable = data["omittable"];
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "target_slot": int.parse(targetSlot.value),
      "predicate": predicate.toJSONEncodable(),
      "sorter": sorter.toJSONEncodable(),
      "omittable": omittable,
    };
  }
}

class EquipmentDeployment extends Observable {
  @observable ShipPredicate shipPredicate;
  @observable final ObservableList<EquipmentRequirement> requirements =
      new ObservableList<EquipmentRequirement>();

  EquipmentDeployment() {
    shipPredicate = new ShipPredicate.fromTRUE();
  }

  EquipmentDeployment.fromJSON(Map<String, dynamic> data) {
    shipPredicate = new ShipPredicate.fromJSON(data["ship_predicate"]);
    for (var requirement in data["requirements"]) {
      requirements.add(new EquipmentRequirement.fromJSON(requirement));
    }
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "ship_predicate": shipPredicate.toJSONEncodable(),
      "requirements": requirements
          .map((requirement) => requirement.toJSONEncodable())
          .toList(),
    };
  }
}

class EquipmentGeneralDeployment extends Observable {
  @observable String name;
  @observable final List<EquipmentDeployment> deployments =
      new ObservableList<EquipmentDeployment>();

  EquipmentGeneralDeployment(this.name);

  EquipmentGeneralDeployment.fromJSON(Map<String, dynamic> data) {
    name = data["name"];
    for (var deployment in data["deployments"]) {
      deployments.add(new EquipmentDeployment.fromJSON(deployment));
    }
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "name": name,
      "deployments": deployments
          .map((deployment) => deployment.toJSONEncodable())
          .toList(),
    };
  }
}
