part of kcaa;

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
  };

  @observable int id;
  @observable String name;
  @observable String shipType;
  @observable int level, upgradeLevel;
  @observable String levelClass;
  @observable int experienceGaugeValue;
  @observable String experienceGauge;
  @observable int fuel, fuelCapacity;
  @observable int ammo, ammoCapacity;
  @observable String fuelPercentage, ammoPercentage;
  @observable int vitality;
  @observable int hp, maxHp;
  @observable String hpPercentage;
  @observable int armor, enhancedArmor, maxArmor;
  @observable int firepower, enhancedFirepower, maxFirepower;
  @observable int thunderstroke, enhancedThunderstroke, maxThunderstroke;
  @observable int antiAir, enhancedAntiAir, maxAntiAir;
  @observable String armorClass, firepowerClass, thunderstrokeClass,
                     antiAirClass;
  @observable bool locked;
  @observable String lockedClass;
  @observable Fleet belongingFleet;
  @observable String stateClass;

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
        (100 * data["loaded_resource_percentage"]["fuel"]).toStringAsFixed(0);
    ammoPercentage =
        (100 * data["loaded_resource_percentage"]["ammo"]).toStringAsFixed(0);
    hpPercentage = (100.0 * hp / maxHp).toStringAsFixed(0);
    armorClass = enhancedArmor == maxArmor ? "fullyEnhanced" : "";
    firepowerClass = enhancedFirepower == maxFirepower ? "fullyEnhanced" : "";
    thunderstrokeClass =
        enhancedThunderstroke == maxThunderstroke ? "fullyEnhanced" : "";
    antiAirClass = enhancedAntiAir == maxAntiAir ? "fullyEnhanced" : "";
    lockedClass = locked ? "locked" : "";
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
}

void handleShipList(Assistant assistant, Map<String, dynamic> data) {
  for (var shipData in (data["ships"] as Map).values) {
    var ship = assistant.shipMap[shipData["id"]];
    if (ship == null) {
      ship = new Ship();
      assistant.shipMap[shipData["id"]] = ship;
    }
    ship.update(shipData, assistant.fleets);
  }
  var shipsLength = data["ship_order"].length;
  if (assistant.ships.length != shipsLength) {
    if (shipsLength < assistant.ships.length) {
      assistant.ships.removeRange(shipsLength, assistant.ships.length);
    } else {
      for (var i = assistant.ships.length; i < shipsLength; i++) {
        assistant.ships.add(null);
      }
    }
  }
  for (var i = 0; i < shipsLength; i++) {
    var ship = assistant.shipMap[int.parse(data["ship_order"][i])];
    // Update the ship list only when the order has changed.
    // Seems like it requires tremendous amount of load to assign a value to
    // ObservableList, even if the value being assigned is the same as the
    // previous value.
    if (assistant.ships[i] != ship) {
      assistant.ships[i] = ship;
    }
  }
}

void notifyShipList(Assistant assistant) {
  var shipIdsInFleets = new Set.from(assistant.fleets.expand(
      (fleet) => fleet.ships).map((ship) => ship.id));
  for (var ship in assistant.ships) {
    if (shipIdsInFleets.contains(ship.id)) {
      ship.updateBelongingFleet(assistant.fleets);
    } else {
      ship.belongingFleet = null;
    }
  }
}