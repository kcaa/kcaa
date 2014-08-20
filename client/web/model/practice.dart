part of kcaa_model;

class ShipEntry extends Observable {
  @observable int shipId;
  @observable int level;
  @observable String name;
  @observable String shipType;

  ShipEntry();

  ShipEntry.fromData(Map<String, dynamic> data) {
    shipId = data["ship_id"];
    level = data["level"];
    name = data["name"];
    shipType = Ship.SHIP_TYPE_MAP[data["ship_type"]];
  }
}

class Practice extends Observable {
  static final Map<int, String> RESULT_MESSAGE = <int, String>{
    0: "",  // Not yet practiced
    1: "E敗北",
    2: "D敗北",
    3: "C敗北",
    4: "B勝利",
    5: "A勝利",
    6: "S勝利",
  };
  static final Map<int, String> RESULT_CLASS = <int, String>{
    0: "",  // Not yet practiced
    1: "practiceLost",
    2: "practiceLost",
    3: "practiceLost",
    4: "practiceWon",
    5: "practiceWon",
    6: "practiceWon",
  };
  static final Map<int, String> FLEET_TYPE = <int, String>{
    0: "汎用型",
    1: "潜水艦主体型",
    2: "対潜無視型",
    3: "空母主体型",
    4: "戦艦主体型",
    5: "重巡主体型",
    6: "軽巡主体型",
    7: "駆逐艦主体型",
  };
  static final Map<int, String> FORMATION_NAME = <int, String>{
    0: "単縦陣",
    1: "複縦陣",
    2: "輪形陣",
    3: "梯形陣",
    4: "単横陣",
  };
  static final Map<String, int> FORMATION_NAME_REVERSE =
      new ReverseMapBuilder().buildFrom(FORMATION_NAME);

  @observable int id;
  @observable String enemyName;
  @observable String enemyComment;
  @observable int enemyLevel;
  @observable String enemyRank;
  @observable String resultMessage;
  @observable String resultClass;
  @observable String fleetName;
  @observable String fleetType;
  @observable List<ShipEntry> ships = new ObservableList<ShipEntry>();

  Practice();

  void update(Map<String, dynamic> data) {
    id = data["id"];
    enemyName = data["enemy_name"];
    enemyComment = data["enemy_comment"];
    enemyLevel = data["enemy_level"];
    enemyRank = data["enemy_rank"];
    resultMessage = RESULT_MESSAGE[data["result"]];
    resultClass = RESULT_CLASS[data["result"]];
    fleetName = data["fleet_name"];
    fleetType = FLEET_TYPE[data["fleet_type"]];
    ships.clear();
    if (data["ships"] != null) {
      for (var ship in data["ships"]) {
        ships.add(new ShipEntry.fromData(ship));
      }
    }
  }
}

void handlePracticeList(Assistant assistant, AssistantModel model,
                        Map<String, dynamic> data) {
  var practicesLength = data["practices"].length;
  resizeList(model.practices, practicesLength, () => new Practice());
  for (var i = 0; i < practicesLength; i++) {
    model.practices[i].update(data["practices"][i]);
  }
  model.numPracticesDone =
      model.practices.where((p) => p.resultMessage != "").length;
}