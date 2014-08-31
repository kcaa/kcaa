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
    14: "潜水母艦",
    15: "補給艦",
    16: "水上機母艦",
    17: "揚陸艦",
    18: "装甲空母",
    19: "工作艦",
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
    "roomInFirepower": filterRoomInFirepower,
    "roomInThunderstroke": filterRoomInThunderstroke,
    "roomInAntiAir": filterRoomInAntiAir,
    "roomInArmor": filterRoomInArmor,
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
    filtered = true;
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
  // (encyclopedia order). This order is consistent with "Lv" in Kancolle
  // player.
  static int compareByKancolleLevel(Ship a, Ship b) {
    if (a.level != b.level) {
     return a.level.compareTo(b.level);
    }
    return -a.sortOrder.compareTo(b.sortOrder);
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
  for (var id in model.shipMap.keys) {
    if (!presentShips.contains(id)) {
      model.shipMap.remove(id);
    }
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