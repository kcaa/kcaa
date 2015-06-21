part of kcaa_model;

class BuildSlot extends Observable {
  static final int STATE_EMPTY = 0;
  static final int STATE_BUILDING = 2;
  static final int STATE_COMPLETED = 3;
  static final Map<int, String> STATE_MAP = <int, String>{
    STATE_EMPTY: "空き",
    STATE_BUILDING: "建造中",
    STATE_COMPLETED: "建造完了",
  };

  @observable int id;
  @observable Ship ship;
  @observable int fuelSpent, ammoSpent, steelSpent, bauxiteSpent;
  @observable int material;
  @observable int state;
  @observable String stateString;
  @observable bool empty;
  @observable DateTime eta;
  @observable String etaDatetimeString;
  @observable bool completed;

  BuildSlot();

  void update(Map<String, dynamic> data, Map<int, Ship> shipDefinitionMap) {
    id = data["id"];
    ship = shipDefinitionMap[data["ship_def_id"]];
    fuelSpent = data["spent_resource"]["fuel"];
    ammoSpent = data["spent_resource"]["ammo"];
    steelSpent = data["spent_resource"]["steel"];
    bauxiteSpent = data["spent_resource"]["bauxite"];
    material = data["material"];
    state = data["state"];
    stateString = STATE_MAP[state];
    empty = data["empty"];

    // ETA.
    if (data["eta"] != 0) {
      eta = new DateTime.fromMillisecondsSinceEpoch(data["eta"], isUtc: true)
          .toLocal();
      etaDatetimeString = formatShortTime(eta);
    } else {
      eta = null;
      etaDatetimeString = null;
    }
    completed = state == STATE_COMPLETED ||
        (eta != null && eta.isBefore(new DateTime.now()));
  }
}
