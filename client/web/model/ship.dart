part of kcaa_model;

class Variable extends Observable {
  @observable int current;
  @observable int baseline;
  @observable int maximum;
  @observable int extra;

  Variable.fromJSON(Map<String, dynamic> data) {
    current = data["current"];
    baseline = data["baseline"];
    maximum = data["maximum"];
    if (current > maximum) {
      extra = current - maximum;
    }
  }

  int cappedCurrent() {
    return current > maximum ? maximum : current;
  }

  double ratio() {
    return current.toDouble() / maximum;
  }

  String percentage() {
    return (100.0 * ratio()).toStringAsFixed(0);
  }
}

class Ship extends Observable {
  static final Map<int, String> SHIP_TYPE_MAP = <int, String>{
    1: "海防艦",
    2: "駆逐艦",
    3: "軽巡洋艦",
    4: "重雷装巡洋艦",
    5: "重巡洋艦",
    6: "航空巡洋艦",
    7: "軽空母",
    8: "高速戦艦",
    9: "戦艦",
    10: "航空戦艦",
    11: "正規空母",
    12: "超弩級戦艦",
    13: "潜水艦",
    14: "潜水空母",
    15: "補給艦",
    16: "水上機母艦",
    17: "揚陸艦",
    18: "装甲空母",
    19: "工作艦",
    20: "潜水母艦",
  };

  static final SHIP_COMPARER = <String, ShipComparer>{
    "name": compareByName,
    "level": compareByKancolleLevel,
    "fuel": compareByFuel,
    "ammo": compareByAmmo,
    "vitality": compareByVitality,
    "hp": compareByHp,
    "firepower": compareByFirepower,
    "thunderstroke": compareByThunderstroke,
    "antiair": compareByAntiAir,
    "armor": compareByArmor,
  };

  static final SHIP_FILTER = <String, ShipFilterer>{
    "none": filterNone,
    "battleship": makeFilterByShipType(["高速戦艦", "戦艦", "航空戦艦", "超弩級戦艦"]),
    "aircraftCarrier": makeFilterByShipType(["正規空母"]),
    "lightAircraftCarrier": makeFilterByShipType(["軽空母"]),
    "heavyCruiser": makeFilterByShipType(["重巡洋艦", "航空巡洋艦"]),
    "torpedoCruiser": makeFilterByShipType(["重雷装巡洋艦"]),
    "lightCruiser": makeFilterByShipType(["軽巡洋艦"]),
    "destroyer": makeFilterByShipType(["駆逐艦"]),
    "submarine": makeFilterByShipType(["潜水艦", "潜水母艦"]),
    "otherShipTypes": makeFilterByShipType(
        ["海防艦", "補給艦", "水上機母艦", "揚陸艦", "装甲空母", "工作艦"]),
    "goodState": makeFilterByState("good"),
    "normalState": makeFilterByState(""),
    "dangerousState": makeFilterByState("dangerous"),
    "fatalState": makeFilterByState("fatal"),
    "canWarmUp": filterCanWarmUp,
    "roomInFirepower": filterRoomInFirepower,
    "roomInThunderstroke": filterRoomInThunderstroke,
    "roomInAntiAir": filterRoomInAntiAir,
    "roomInArmor": filterRoomInArmor,
    "locked": filterLocked,
    "notLocked": filterNotLocked,
  };

  @observable int id;
  @observable String name;
  @observable String shipType;
  @observable int level, upgradeLevel;
  @observable String levelClass;
  @observable int experienceGaugeValue;
  @observable String experienceGauge;
  @observable int fuel, fuelCapacity, fuelPercentage;
  @observable int ammo, ammoCapacity, ammoPercentage;
  @observable String fuelPercentageString, ammoPercentageString;
  @observable int vitality;
  @observable int hp, maxHp, hpPercentage;
  @observable String hpPercentageString;
  @observable Variable firepower, thunderstroke, antiAir, armor;
  @observable int enhancedFirepower, enhancedThunderstroke, enhancedAntiAir,
    enhancedArmor;
  @observable String firepowerClass, thunderstrokeClass, antiAirClass,
    armorClass;
  @observable Variable antiSubmarine, avoidance, scouting, luck;
  @observable bool locked;
  @observable bool isUnderRepair;
  @observable bool awayForMission;
  @observable List<String> tags = new ObservableList<String>();
  @observable String lockedClass;
  @observable Fleet belongingFleet;
  @observable String stateClass;
  @observable int sortOrder;

  Ship();

  void update(Map<String, dynamic> data, List<Fleet> fleets) {
    id = data["id"];
    name = data["name"];
    shipType = SHIP_TYPE_MAP[data["ship_type"]];
    level = data["level"];
    upgradeLevel = data["upgrade_level"];
    fuel = data["loaded_resource"]["fuel"];
    fuelCapacity = data["resource_capacity"]["fuel"];
    ammo = data["loaded_resource"]["ammo"];
    ammoCapacity = data["resource_capacity"]["ammo"];
    vitality = data["vitality"];
    hp = data["hitpoint"]["current"];
    maxHp = data["hitpoint"]["maximum"];
    firepower = new Variable.fromJSON(data["firepower"]);
    enhancedFirepower =
        firepower.baseline + data["enhanced_ability"]["firepower"];
    thunderstroke = new Variable.fromJSON(data["thunderstroke"]);
    enhancedThunderstroke =
      thunderstroke.baseline + data["enhanced_ability"]["thunderstroke"];
    antiAir = new Variable.fromJSON(data["anti_air"]);
    enhancedAntiAir = antiAir.baseline + data["enhanced_ability"]["anti_air"];
    armor = new Variable.fromJSON(data["armor"]);
    enhancedArmor = armor.baseline + data["enhanced_ability"]["armor"];
    // TODO: Is there any way to obtain enhanced amount for these parameters?
    antiSubmarine = new Variable.fromJSON(data["anti_submarine"]);
    avoidance = new Variable.fromJSON(data["avoidance"]);
    scouting = new Variable.fromJSON(data["scouting"]);
    luck = new Variable.fromJSON(data["luck"]);
    locked = data["locked"];
    isUnderRepair = data["is_under_repair"];
    awayForMission = data["away_for_mission"];
    if (data["tags"] == null) {
      tags.clear();
    }
    if (data["tags"] != null && !iterableEquals(tags, data["tags"])) {
      tags.clear();
      tags.addAll(data["tags"]);
    }

    levelClass = upgradeLevel != 0 && level >= upgradeLevel ? "upgradable" : "";
    // What?! Dart doesn't have something similar to sprintf...
    // Neither in string interpolation......
    if (data.containsKey("experience_gauge")) {
      experienceGaugeValue = data["experience_gauge"];
      experienceGauge = experienceGaugeValue.toString();
      if (experienceGaugeValue < 10) {
        experienceGauge = "0" + experienceGauge;
      }
    }
    fuelPercentage =
        10 * (10 * data["loaded_resource_percentage"]["fuel"]).round();
    fuelPercentageString = fuelPercentage.toStringAsFixed(0);
    ammoPercentage =
        10 * (10 * data["loaded_resource_percentage"]["ammo"]).round();
    ammoPercentageString = ammoPercentage.toStringAsFixed(0);
    hpPercentage = (100 * hp / maxHp).round();
    hpPercentageString = hpPercentage.toString();
    firepowerClass =
        enhancedFirepower == firepower.maximum ? "fullyEnhanced" : "";
    thunderstrokeClass =
        enhancedThunderstroke == thunderstroke.maximum ? "fullyEnhanced" : "";
    antiAirClass = enhancedAntiAir == antiAir.maximum ? "fullyEnhanced" : "";
    armorClass = enhancedArmor == armor.maximum ? "fullyEnhanced" : "";
    lockedClass = locked ? "" : "unlocked";
    updateBelongingFleet(fleets);
    stateClass = getStateClass();
  }

  String getStateClass() {
    if (hp / maxHp <= 0.25 || vitality < 20) {
      return "fatal";
    } else if (hp / maxHp <= 0.5 || vitality < 30) {
      return "dangerous";
    } else if (vitality >= 50) {
      return "good";
    } else {
      return "";
    }
  }

  void updateBelongingFleet(List<Fleet> fleets) {
    for (var fleet in fleets){
      if (fleet.ships.any((fleetShip) => fleetShip.id == id)) {
        belongingFleet = fleet;
        return;
      }
    }
    belongingFleet = null;
  }

  static int compareByName(Ship a, Ship b) {
    if (a.name != b.name) {
      return a.name.compareTo(b.name);
    }
    return compareByKancolleLevel(a, b);
  }

  // Compare ships by Kancolle level.
  // First sort by level (not considering experience gauge), then by sort order
  // (encyclopedia order), and then the ship instance ID. This order is
  // consistent with "Lv" in Kancolle player.
  static int compareByKancolleLevel(Ship a, Ship b) {
    if (a.level != b.level) {
     return a.level.compareTo(b.level);
    } else if (a.sortOrder != b.sortOrder) {
      return -a.sortOrder.compareTo(b.sortOrder);
    } else {
      return -a.id.compareTo(b.id);
    }
  }

  static int compareByFuel(Ship a, Ship b) {
    if (a.fuelPercentage != b.fuelPercentage) {
      return a.fuelPercentage.compareTo(b.fuelPercentage);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByAmmo(Ship a, Ship b) {
    if (a.ammoPercentage != b.ammoPercentage) {
      return a.ammoPercentage.compareTo(b.ammoPercentage);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByVitality(Ship a, Ship b) {
    if (a.vitality != b.vitality) {
      return a.vitality.compareTo(b.vitality);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByHp(Ship a, Ship b) {
    if (a.hpPercentage != b.hpPercentage) {
      return a.hpPercentage.compareTo(b.hpPercentage);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByFirepower(Ship a, Ship b) {
    if (a.firepower.current != b.firepower.current) {
      return a.firepower.current.compareTo(b.firepower.current);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByThunderstroke(Ship a, Ship b) {
    if (a.thunderstroke.current != b.thunderstroke.current) {
      return a.thunderstroke.current.compareTo(b.thunderstroke.current);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByAntiAir(Ship a, Ship b) {
    if (a.antiAir.current != b.antiAir.current) {
      return a.antiAir.current.compareTo(b.antiAir.current);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByArmor(Ship a, Ship b) {
    if (a.armor.current != b.armor.current) {
      return a.armor.current.compareTo(b.armor.current);
    }
    return compareByKancolleLevel(a, b);
  }

  // Inverse the sort order; ships are sorted in descending order.
  static int orderInDescending(int result) {
    return -result;
  }

  // Respect the sort order; ships are sorted in ascending order.
  static int orderInAscending(int result) {
    return result;
  }

  static bool filterNone(Ship s) {
    return true;
  }

  static ShipFilterer makeFilterByShipType(List<int> shipTypes) {
    var shipTypeSet = shipTypes.toSet();
    return (Ship s) => shipTypeSet.contains(s.shipType);
  }

  static ShipFilterer makeFilterByState(String stateClass) {
    return (Ship s) => s.stateClass == stateClass;
  }

  static bool filterCanWarmUp(Ship s) {
    return (s.stateClass == "good" || s.stateClass == "") &&
        s.vitality < Fleet.WARMUP_VITALITY;
  }

  static bool filterRoomInFirepower(Ship s) {
    return s.enhancedFirepower < s.firepower.maximum;
  }

  static bool filterRoomInThunderstroke(Ship s) {
    return s.enhancedThunderstroke < s.thunderstroke.maximum;
  }

  static bool filterRoomInAntiAir(Ship s) {
    return s.enhancedAntiAir < s.antiAir.maximum;
  }

  static bool filterRoomInArmor(Ship s) {
    return s.enhancedArmor < s.armor.maximum;
  }

  static bool filterLocked(Ship s) {
    return s.locked;
  }

  static bool filterNotLocked(Ship s) {
    return !s.locked;
  }
}

class ShipPropertyFilter extends Observable {
  @observable KSelection property = new KSelection.from(
      [["id", "艦船"],
       ["ship_id", "艦名"],
       ["signature", "進化系統"],
       ["ship_type", "艦種"],
       ["level", "レベル"],
       ["resource_capacity.fuel", "燃料積載量"],
       ["resource_capacity.ammo", "弾薬積載量"],
       ["hitpoint.percentage", "HP %"],
       ["hitpoint.maximum", "最大HP"],
       ["vitality", "戦意"],
       ["firepower.current", "火力"],
       ["thunderstroke.current", "雷装"],
       ["anti_air.current", "対空"],
       ["armor.current", "装甲"],
       ["avoidance.current", "回避"],
       ["anti_submarine.current", "対潜"],
       ["scouting.current", "索敵"],
       ["luck.current", "運"],
       ["speed", "航行速度"],
       ["firing_range", "射程"],
       ["slot_count", "装備スロット数"],
       ["ready", "出撃可能"],
       ["locked", "ロック"],
       ["is_under_repair", "修理中"],
       ["away_for_mission", "遠征中"]]);
  @observable String value;
  @observable KSelection operator = new KSelection.from(
      [["0", "="],
       ["1", "!="],
       ["2", "<"],
       ["3", "<="],
       ["4", ">"],
       ["5", ">="]]);
  static bool parseBool(String value) => value == "true";
  static final Map<String, Function> VALUE_PARSER_MAP = <String, Function> {
    "id": int.parse,
    "ship_id": int.parse,
    "signature": int.parse,
    "ship_type": int.parse,
    "level": int.parse,
    "resource_capacity.fuel": int.parse,
    "resource_capacity.ammo": int.parse,
    "hitpoint.percentage": int.parse,
    "hitpoint.maximum": int.parse,
    "vitality": int.parse,
    "firepower.current": int.parse,
    "thunderstroke.current": int.parse,
    "anti_air.current": int.parse,
    "armor.current": int.parse,
    "avoidance.current": int.parse,
    "anti_submarine.current": int.parse,
    "scouting.current": int.parse,
    "luck.current": int.parse,
    "speed": int.parse,
    "firing_range": int.parse,
    "slot_count": int.parse,
    "ready": parseBool,
    "locked": parseBool,
    "is_under_repair": parseBool,
    "away_for_mission": parseBool,
  };

  ShipPropertyFilter.shipId(int id) {
    property.value = "id";
    value = id.toString();
    operator.value = "0";
  }

  ShipPropertyFilter.fromJSON(Map<String, dynamic> data) {
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

class TagFilter extends Observable {
  @observable String tag;
  @observable KSelection operator = new KSelection.from(
      [["0", "を含む"],
       ["1", "を含まない"]]);

  TagFilter.contains(this.tag) {
    operator.value = "0";
  }

  TagFilter.notContains(this.tag) {
    operator.value = "1";
  }

  TagFilter.fromJSON(Map<String, dynamic> data) {
    tag = data["tag"];
    operator.value = data["operator"].toString();
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "tag": tag,
      "operator": int.parse(operator.value),
    };
  }
}

class ShipFilter extends Observable {
  ShipFilter.fromJSON(Map<String, dynamic> data) {
  }

  Map<String, dynamic> toJSONEncodable() {
    return null;
  }
}

class ShipPredicate extends Observable {
  @observable KSelection type = new KSelection.from(
      [["true", "TRUE"],
       ["false", "FALSE"],
       ["or", "OR"],
       ["and", "AND"],
       ["not", "NOT"],
       ["propertyFilter", "プロパティフィルタ"],
       ["tagFilter", "タグフィルタ"],
       ["filter", "定義済みフィルタ"]]);
  @observable bool true_ = false;
  @observable bool false_ = false;
  @observable final List<ShipPredicate> or =
      new ObservableList<ShipPredicate>();
  @observable final List<ShipPredicate> and =
      new ObservableList<ShipPredicate>();
  @observable ShipPredicate not;
  @observable ShipPropertyFilter propertyFilter =
      new ShipPropertyFilter.shipId(0);
  @observable TagFilter tagFilter = new TagFilter.contains("");
  @observable ShipFilter filter;

  ShipPredicate.fromTRUE() {
    type.value = "true";
    true_ = true;
  }

  ShipPredicate.fromFALSE() {
    type.value = "false";
    false_ = true;
  }

  ShipPredicate.fromOR(Iterable<ShipPredicate> predicates) {
    type.value = "or";
    or.addAll(predicates);
  }

  ShipPredicate.fromAND(Iterable<ShipPredicate> predicates) {
    type.value = "and";
    and.addAll(predicates);
  }

  ShipPredicate.fromNOT(this.not) {
    type.value = "not";
  }

  ShipPredicate.fromPropertyFilter(this.propertyFilter) {
    type.value = "propertyFilter";
  }

  ShipPredicate.fromTagFilter(this.tagFilter) {
    type.value = "tagFilter";
  }

  ShipPredicate.fromFilter(this.filter) {
    type.value = "filter";
  }

  ShipPredicate.fromJSON(Map<String, dynamic> data) {
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
        or.add(new ShipPredicate.fromJSON(orData));
      }
    } else if (data["and"] != null) {
      type.value = "and";
      for (var andData in data["and"]) {
        and.add(new ShipPredicate.fromJSON(andData));
      }
    } else if (data["not"] != null) {
      type.value = "not";
      not = new ShipPredicate.fromJSON(data["not"]);
    } else if (data["property_filter"] != null) {
      type.value = "propertyFilter";
      propertyFilter = new ShipPropertyFilter.fromJSON(data["property_filter"]);
    } else if (data["tag_filter"] != null) {
      type.value = "tagFilter";
      tagFilter = new TagFilter.fromJSON(data["tag_filter"]);
    } else if (data["filter"] != null) {
      type.value = "filter";
      filter = new ShipFilter.fromJSON(data["filter"]);
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
      return {"or": or.map((predicate) =>
          predicate.toJSONEncodable()).toList()};
    } else if (type.value == "and") {
      return {"and": and.map((predicate) =>
          predicate.toJSONEncodable()).toList()};
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

class ShipSorter extends Observable {
  @observable final KSelection name = new KSelection.from(
      [["kancolle_level", "レベル"],
       ["hitpoint_ratio", "HP %"],
       ["rebuilding_rank", "近代化改修の価値"]]);
  @observable final KSelection reversed = new KSelection.from(
      [["true", "一番高い"],
       ["false", "一番低い"]]);

  ShipSorter(String name, bool reversed) {
    this.name.value = name;
    this.reversed.value = reversed.toString();
  }

  ShipSorter.level(bool reversed) {
    name.value = "kancolle_level";
    this.reversed.value = reversed.toString();
  }

  ShipSorter.fromJSON(Map<String, dynamic> data) {
    name.value = data["name"];
    reversed.value = data["reversed"].toString();
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "name": name.value,
      "reversed": reversed.value == "true",
    };
  }
}

class ShipRequirement extends Observable {
  @observable ShipPredicate predicate;
  @observable ShipSorter sorter;
  @observable bool omittable;

  ShipRequirement(this.predicate, this.sorter, this.omittable);
}

void handleShipList(Assistant assistant, AssistantModel model,
                    Map<String, dynamic> data) {
  Set<int> presentShips = new Set<int>();
  for (var shipData in (data["ships"] as Map).values) {
    var id = shipData["id"];
    var ship = model.shipMap[id];
    if (ship == null) {
      ship = new Ship();
      model.shipMap[id] = ship;
    }
    ship.update(shipData, model.fleets);
    presentShips.add(id);
  }
  // Remove ships that are no longer available.
  Set<int> removedShips =
      new Set<int>.from(model.shipMap.keys).difference(presentShips);
  for (var id in removedShips) {
    model.shipMap.remove(id);
  }
  reorderShipList(model);
  model.numFilteredShips =
      model.ships.where((ship) => model.shipList.filter(ship)).length;
}

void reorderShipList(AssistantModel model) {
  var shipsLength = model.shipMap.length;
  resizeList(model.ships, shipsLength, () => new Ship());
  var sortedShips = model.shipMap.values.toList(growable: false);
  var inverter = model.shipList.shipOrderInverter;
  var comparer = model.shipList.shipComparer;
  sortedShips.sort((a, b) => inverter(comparer(a, b)));
  for (var i = 0; i < shipsLength; i++) {
    var ship = sortedShips[i];
    // Update the ship list only when the order has changed.
    // Seems like it requires tremendous amount of load to assign a value to
    // ObservableList, even if the value being assigned is the same as the
    // previous value.
    if (model.ships[i] != ship) {
      model.ships[i] = ship;
    }
  }
}

void notifyShipList(AssistantModel model) {
  var shipIdsInFleets = new Set.from(model.fleets.expand(
      (fleet) => fleet.ships).map((ship) => ship.id));
  for (var ship in model.ships) {
    if (shipIdsInFleets.contains(ship.id)) {
      ship.updateBelongingFleet(model.fleets);
    } else {
      ship.belongingFleet = null;
    }
  }
}

void handleShipDefinitionList(Assistant assistant, AssistantModel model,
                              Map<String, dynamic> data) {
  for (var shipData in (data["ships"] as Map).values) {
    var ship = new Ship();
    ship.id = shipData["id"];
    ship.name = shipData["name"];
    ship.shipType = Ship.SHIP_TYPE_MAP[shipData["ship_type"]];
    model.shipDefinitionMap[ship.id] = ship;
  }
}
