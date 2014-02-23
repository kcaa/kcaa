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
  int level;
  int fuel, fuelCapacity;
  int ammo, ammoCapacity;
  String fuelPercentage, ammoPercentage;
  int vitality;
  int hp, maxHp;
  String hpPercentage;
  String stateClass;

  Ship(Map<String, dynamic> data)
      : id = data["id"],
        name = data["name"],
        shipType = SHIP_TYPE_MAP[data["ship_type"]],
        level = data["level"],
        fuel = data["loaded_resource"]["fuel"],
        fuelCapacity = data["resource_capacity"]["fuel"],
        ammo = data["loaded_resource"]["ammo"],
        ammoCapacity = data["resource_capacity"]["ammo"],
        vitality = data["vitality"],
        hp = data["hitpoint"]["current"],
        maxHp = data["hitpoint"]["maximum"],
        stateClass = "" {
    fuelPercentage = (100.0 * fuel / fuelCapacity).toStringAsFixed(0);
    ammoPercentage = (100.0 * ammo / ammoCapacity).toStringAsFixed(0);
    hpPercentage = (100.0 * hp / maxHp).toStringAsFixed(0);
  }
}

void handleShipList(Assistant assistant, Map<String, dynamic> data) {
  assistant.ships.clear();
  var ships = new List.from(data["ships"].values, growable: false);
  ships.sort((x, y) => -x["level"].compareTo(y["level"]));
  for (var shipData in ships) {
    assistant.ships.add(new Ship(shipData));
  }
}