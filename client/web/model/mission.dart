part of kcaa_model;

class Mission extends Observable {
  static final Map<int, String> DIFFICULTY_MAP = <int, String>{
    1: "E",
    2: "D",
    3: "C",
    4: "B",
    5: "A",
    6: "S", // S
    7: "S", // SS
    8: "S", // SSS
  };
  static final Map<int, String> MAPAREA_MAP = <int, String>{
    1: "鎮守府",
    2: "南西諸島",
    3: "北方",
    4: "西方",
    5: "南方",
    26: "索敵機",
    27: "AL/MI",
  };
  static final Map<int, String> STATE_CLASS_MAP = <int, String>{
    -1: "disabled",
    0: "new",
    1: "new",
    2: "",
  };

  @observable int id;
  @observable String name;
  @observable String description;
  @observable String difficulty;
  @observable String maparea;
  @observable int state;
  @observable String stateClass;
  @observable int time;
  @observable int fuelConsumption;
  @observable int ammoConsumption;
  @observable int fuel, ammo, steel, bauxite;
  @observable int undertakingFleetId;
  @observable String undertakingFleetName;
  @observable DateTime eta;
  @observable String etaDatetimeString;

  Mission();

  void update(Map<String, dynamic> data) {
    id = data["id"];
    name = data["name"];
    description = data["description"];
    difficulty = DIFFICULTY_MAP[data["difficulty"]];
    maparea = MAPAREA_MAP[data["maparea"]];
    state = data["state"];
    stateClass = STATE_CLASS_MAP[data["state"]];
    time = data["time"];
    fuelConsumption = (data["consumption"]["fuel"] * 100).toInt();
    ammoConsumption = (data["consumption"]["ammo"] * 100).toInt();
    data["rewards"].putIfAbsent("fuel", () => 0);
    data["rewards"].putIfAbsent("ammo", () => 0);
    data["rewards"].putIfAbsent("steel", () => 0);
    data["rewards"].putIfAbsent("bauxite", () => 0);
    fuel = data["rewards"]["fuel"];
    ammo = data["rewards"]["ammo"];
    steel = data["rewards"]["steel"];
    bauxite = data["rewards"]["bauxite"];

    // Undertaking fleet.
    if (data["undertaking_fleet"] != null) {
      undertakingFleetId = data["undertaking_fleet"][0];
      undertakingFleetName = data["undertaking_fleet"][1];
      stateClass = "active";
    } else {
      undertakingFleetId = -1;
    }

    // ETA.
    if (data["eta"] != null) {
      eta = new DateTime.fromMillisecondsSinceEpoch(data["eta"], isUtc: true)
          .toLocal();
      etaDatetimeString = formatShortTime(eta);
    }
  }
}
