part of kcaa_model;

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
  @observable int armor, enhancedArmor, maxArmor;
  @observable int firepower, enhancedFirepower, maxFirepower;
  @observable int thunderstroke, enhancedThunderstroke, maxThunderstroke;
  @observable int antiAir, enhancedAntiAir, maxAntiAir;
  @observable String armorClass, firepowerClass, thunderstrokeClass,
                     antiAirClass;
  @observable bool locked;
  @observable bool isUnderRepair;
  @observable String lockedClass;
  @observable Fleet belongingFleet;
  @observable String stateClass;
  @observable int sortOrder;
  // Whether filtered or not. Only filtered ships are shown in the list.
  @observable bool filtered;

  Ship();

  void update(Map<String, dynamic> data, List<Fleet> fleets,
              ShipFilterer filter) {
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
    armor = data["armor"]["current"];
    enhancedArmor =
      data["armor"]["baseline"] + data["enhanced_ability"]["armor"];
    maxArmor = data["armor"]["maximum"];
    firepower = data["firepower"]["current"];
    enhancedFirepower =
      data["firepower"]["baseline"] + data["enhanced_ability"]["firepower"];
    maxFirepower = data["firepower"]["maximum"];
    thunderstroke = data["thunderstroke"]["current"];
    enhancedThunderstroke =
      data["thunderstroke"]["baseline"] +
      data["enhanced_ability"]["thunderstroke"];
    maxThunderstroke = data["thunderstroke"]["maximum"];
    antiAir = data["anti_air"]["current"];
    enhancedAntiAir =
      data["anti_air"]["baseline"] + data["enhanced_ability"]["anti_air"];
    maxAntiAir = data["anti_air"]["maximum"];
    locked = data["locked"];
    isUnderRepair = data["is_under_repair"];

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
    armorClass = enhancedArmor == maxArmor ? "fullyEnhanced" : "";
    firepowerClass = enhancedFirepower == maxFirepower ? "fullyEnhanced" : "";
    thunderstrokeClass =
        enhancedThunderstroke == maxThunderstroke ? "fullyEnhanced" : "";
    antiAirClass = enhancedAntiAir == maxAntiAir ? "fullyEnhanced" : "";
    lockedClass = locked ? "" : "unlocked";
    updateBelongingFleet(fleets);
    stateClass = getStateClass();
    sortOrder = data["sort_order"];
    filtered = filter(this);
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
    if (a.firepower != b.firepower) {
      return a.firepower.compareTo(b.firepower);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByThunderstroke(Ship a, Ship b) {
    if (a.thunderstroke != b.thunderstroke) {
      return a.thunderstroke.compareTo(b.thunderstroke);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByAntiAir(Ship a, Ship b) {
    if (a.antiAir != b.antiAir) {
      return a.antiAir.compareTo(b.antiAir);
    }
    return compareByKancolleLevel(a, b);
  }

  static int compareByArmor(Ship a, Ship b) {
    if (a.armor != b.armor) {
      return a.armor.compareTo(b.armor);
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
    return s.enhancedFirepower < s.maxFirepower;
  }

  static bool filterRoomInThunderstroke(Ship s) {
    return s.enhancedThunderstroke < s.maxThunderstroke;
  }

  static bool filterRoomInAntiAir(Ship s) {
    return s.enhancedAntiAir < s.maxAntiAir;
  }

  static bool filterRoomInArmor(Ship s) {
    return s.enhancedArmor < s.maxArmor;
  }

  static bool filterLocked(Ship s) {
    return s.locked;
  }

  static bool filterNotLocked(Ship s) {
    return !s.locked;
  }
}

class ShipPropertyFilter extends Observable {
  @observable String property;
  @observable dynamic value;
  @observable int operator;
  static final Map<int, String> OPERATOR_MAP = <int, String>{
    0: "=",
    1: "!=",
    2: "<",
    3: "<=",
    4: ">",
    5: ">=",
  };
  static const int OPERATOR_EQUAL = 0;
  static const int OPERATOR_NOT_EQUAL = 1;
  static const int OPERATOR_LESS_THAN= 2;
  static const int OPERATOR_LESS_THAN_EQUAL = 3;
  static const int OPERATOR_GREATER_THAN = 4;
  static const int OPERATOR_GREATER_THAN_EQUAL = 5;

  ShipPropertyFilter(this.property, this.value, this.operator);

  ShipPropertyFilter.shipId(int id) {
    property = "id";
    value = id;
    operator = OPERATOR_EQUAL;
  }

  ShipPropertyFilter.fromJSON(Map<String, dynamic> data) {
    property = data["property"];
    value = data["value"];
    operator = data["operator"];
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "property": property,
      "value": value,
      "operator": operator,
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
  @observable final List<ShipPredicate> or =
      new ObservableList<ShipPredicate>();
  @observable final List<ShipPredicate> and =
      new ObservableList<ShipPredicate>();
  @observable ShipPredicate not;
  @observable ShipPropertyFilter propertyFilter;
  @observable ShipFilter filter;

  ShipPredicate.fromOR(Iterable<ShipPredicate> predicates) {
    or.addAll(predicates);
  }

  ShipPredicate.fromAND(Iterable<ShipPredicate> predicates) {
    and.addAll(predicates);
  }

  ShipPredicate.fromNOT(this.not);

  ShipPredicate.fromPropertyFilter(this.propertyFilter);

  ShipPredicate.fromFilter(this.filter);

  ShipPredicate.fromJSON(Map<String, dynamic> data) {
    if (data == null) {
      return;
    }
    if (data.containsKey("or")) {
      for (var orData in data["or"]) {
        or.add(new ShipPredicate.fromJSON(orData));
      }
    }
    if (data.containsKey("and")) {
      for (var andData in data["and"]) {
        and.add(new ShipPredicate.fromJSON(andData));
      }
    }
    if (data.containsKey("not")) {
      not = new ShipPredicate.fromJSON(data["not"]);
    }
    if (data.containsKey("property_filter")) {
      propertyFilter = new ShipPropertyFilter.fromJSON(data["property_filter"]);
    }
    if (data.containsKey("filter")) {
      filter = new ShipFilter.fromJSON(data["filter"]);
    }
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "or": !or.isEmpty ?
          or.map((predicate) => predicate.toJSONEncodable()).toList() : null,
      "and": !and.isEmpty ?
          and.map((predicate) => predicate.toJSONEncodable()).toList() : null,
      "not": not != null ? not.toJSONEncodable() : null,
      "property_filter":
        propertyFilter != null ? propertyFilter.toJSONEncodable() : null,
      "filter": filter != null ? filter.toJSONEncodable() : null,
    };
  }
}

class ShipSorter extends Observable {
  @observable String name;
  @observable bool reversed;

  ShipSorter(this.name, this.reversed);

  ShipSorter.level(this.reversed) {
    name = "kancolle_level";
  }

  ShipSorter.fromJSON(Map<String, dynamic> data) {
    name = data["name"];
    reversed = data["reversed"];
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "name": name,
      "reversed": reversed,
    };
  }
}

void handleShipList(Assistant assistant, AssistantModel model,
                    Map<String, dynamic> data) {
  Set<int> presentShips = new Set<int>();
  int numFilteredShips = 0;
  for (var shipData in (data["ships"] as Map).values) {
    var id = shipData["id"];
    var ship = model.shipMap[id];
    if (ship == null) {
      ship = new Ship();
      model.shipMap[id] = ship;
    }
    ship.update(shipData, model.fleets, model.shipFilter);
    presentShips.add(id);
    numFilteredShips += ship.filtered ? 1 : 0;
  }
  model.numFilteredShips = numFilteredShips;
  // Remove ships that are no longer available.
  Set<int> removedShips =
      new Set<int>.from(model.shipMap.keys).difference(presentShips);
  for (var id in removedShips) {
    model.shipMap.remove(id);
  }
  reorderShipList(model);
}

void reorderShipList(AssistantModel model) {
  var shipsLength = model.shipMap.length;
  resizeList(model.ships, shipsLength, () => new Ship());
  var sortedShips = model.shipMap.values.toList(growable: false);
  sortedShips.sort((a, b) => model.shipOrderInverter(model.shipComparer(a, b)));
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
