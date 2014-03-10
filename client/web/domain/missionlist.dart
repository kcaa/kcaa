part of kcaa;

class Mission extends Observable {
  static final Map<int, String> DIFFICULTY_MAP = <int, String>{
    1: "E",
    2: "D",
    3: "C",
    4: "B",
    5: "A",
    6: "S",  // S
    7: "S",  // SS
    8: "S",  // SSS
  };
  static final Map<int, String> MAPAREA_MAP = <int, String>{
    1: "鎮守府",
    2: "南西諸島",
    3: "北方",
    4: "西方",
    5: "南方",
  };
  static final Map<int, String> STATE_CLASS_MAP = <int, String>{
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
  @observable int undertakingFleetId;
  @observable String undertakingFleetName;
  @observable DateTime eta;
  @observable String etaDatetimeString;

  Mission(Map<String, dynamic> data)
      : id = data["id"],
        name = data["name"],
        description = data["description"],
        difficulty = DIFFICULTY_MAP[data["difficulty"]],
        maparea = MAPAREA_MAP[data["maparea"]],
        state = data["state"],
        stateClass = STATE_CLASS_MAP[data["state"]],
        time = data["time"],
        fuelConsumption =
          (data["consumption"]["fuel"] * 100).toStringAsFixed(0),
        ammoConsumption =
          (data["consumption"]["ammo"] * 100).toStringAsFixed(0) {
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
      var etaDate = new DateTime(eta.year, eta.month, eta.day);
      var now = new DateTime.now();
      var today = new DateTime(now.year, now.month, now.day);
      if (etaDate == today) {
        etaDatetimeString = new DateFormat.Hm("ja_JP").format(eta);
      } else {
        etaDatetimeString = new DateFormat.MMMd("ja_JP").add_Hm().format(eta);
      }
    }
  }
}

void handleMissionList(Assistant assistant, Map<String, dynamic> data) {
  assistant.missions.clear();
  for (var missionData in data["missions"]) {
    if (missionData["name"] != null) {
      assistant.missions.add(new Mission(missionData));
    }
  }
}