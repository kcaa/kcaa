part of kcaa;

class Mission {
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
  static final Map<int, String> STATE_MAP = <int, String>{
    0: "new",
    1: "new",
    2: "",
  };

  int id;
  String name;
  String description;
  String difficulty;
  String maparea;
  String state;
  int time;
  double fuelConsumption;
  double ammoConsumption;
  int undertakingFleetId;
  String undertakingFleetName;
  DateTime eta;
  String etaDatetimeString;

  Mission(Map<String, dynamic> data)
      : id = data["id"],
        name = data["name"],
        description = data["description"],
        difficulty = DIFFICULTY_MAP[data["difficulty"]],
        maparea = MAPAREA_MAP[data["maparea"]],
        state = STATE_MAP[data["state"]],
        time = data["time"],
        fuelConsumption = data["fuel_consumption"],
        ammoConsumption = data["ammo_consumption"] {
    // Undertaking fleet.
    if (data["undertaking_fleet"] != null) {
      undertakingFleetId = data["undertaking_fleet"][0];
      undertakingFleetName = data["undertaking_fleet"][1];
      state = "active";
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
    if (missionData["name"] != "") {
      assistant.missions.add(new Mission(missionData));
    }
  }
}