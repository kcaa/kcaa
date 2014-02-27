part of kcaa;

class Ship {
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

  int id;
  String name;
  String shipType;
  int level, upgradeLevel;
  String levelClass;
  int experienceGaugeValue;
  String experienceGauge;
  int fuel, fuelCapacity;
  int ammo, ammoCapacity;
  String fuelPercentage, ammoPercentage;
  int vitality;
  int hp, maxHp;
  String hpPercentage;
  int armor, enhancedArmor, maxArmor;
  int firepower, enhancedFirepower, maxFirepower;
  int thunderstroke, enhancedThunderstroke, maxThunderstroke;
  int antiAir, enhancedAntiAir, maxAntiAir;
  String armorClass, firepowerClass, thunderstrokeClass, antiAirClass;
  bool locked;
  String lockedClass;
  Fleet belongingFleet;
  String stateClass;

  Ship(Map<String, dynamic> data, List<Fleet> fleets)
      : id = data["id"],
        name = data["name"],
        shipType = SHIP_TYPE_MAP[data["ship_type"]],
        level = data["level"],
        upgradeLevel = data["upgrade_level"],
        fuel = data["loaded_resource"]["fuel"],
        fuelCapacity = data["resource_capacity"]["fuel"],
        ammo = data["loaded_resource"]["ammo"],
        ammoCapacity = data["resource_capacity"]["ammo"],
        vitality = data["vitality"],
        hp = data["hitpoint"]["current"],
        maxHp = data["hitpoint"]["maximum"],
        armor = data["armor"]["current"],
        enhancedArmor =
          data["armor"]["baseline"] + data["enhanced_ability"]["armor"],
        maxArmor = data["armor"]["maximum"],
        firepower = data["firepower"]["current"],
        enhancedFirepower =
          data["firepower"]["baseline"] + data["enhanced_ability"]["firepower"],
        maxFirepower = data["firepower"]["maximum"],
        thunderstroke = data["thunderstroke"]["current"],
        enhancedThunderstroke =
          data["thunderstroke"]["baseline"] +
          data["enhanced_ability"]["thunderstroke"],
        maxThunderstroke = data["thunderstroke"]["maximum"],
        antiAir = data["anti_air"]["current"],
        enhancedAntiAir =
          data["anti_air"]["baseline"] + data["enhanced_ability"]["anti_air"],
        maxAntiAir = data["anti_air"]["maximum"],
        locked = data["locked"] {
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
    fuelPercentage = (100.0 * fuel / fuelCapacity).toStringAsFixed(0);
    ammoPercentage = (100.0 * ammo / ammoCapacity).toStringAsFixed(0);
    hpPercentage = (100.0 * hp / maxHp).toStringAsFixed(0);
    armorClass = enhancedArmor == maxArmor ? "fullyEnhanced" : "";
    firepowerClass = enhancedFirepower == maxFirepower ? "fullyEnhanced" : "";
    thunderstrokeClass =
        enhancedThunderstroke == maxThunderstroke ? "fullyEnhanced" : "";
    antiAirClass = enhancedAntiAir == maxAntiAir ? "fullyEnhanced" : "";
    lockedClass = locked ? "locked" : "";
    // Check the belonging fleet.
    for (var fleet in fleets) {
      for (var ship in fleet.ships) {
        if (ship.id == id) {
          belongingFleet = fleet;
        }
      }
    }
  }
}

void handleShipList(Assistant assistant, Map<String, dynamic> data) {
  assistant.ships.clear();
  assistant.shipMap.clear();
  var ships = new List.from(data["ships"].values, growable: false);
  ships.sort((Map x, Map y) {
    if (x["level"] != y["level"]) {
      return -x["level"].compareTo(y["level"]);
    } else if (x.containsKey("experience_gauge")) {
      return -x["experience_gauge"].compareTo(y["experience_gauge"]);
    } else {
      return 0;
    }
  });
  for (var shipData in ships) {
    var ship = new Ship(shipData, assistant.fleets);
    assistant.ships.add(ship);
    assistant.shipMap[ship.id] = ship;
  }
  notifyFleetList(assistant);
}