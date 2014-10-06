part of kcaa_model;

class BuildSlot extends Observable {
  static final Map<int, String> STATE_MAP = <int, String>{
    0: "空き",
    2: "建造中",
    3: "建造完了",
  };

  @observable int id;
  @observable Ship ship;
  @observable int fuelSpent, ammoSpent, steelSpent, bauxiteSpent;
  @observable int material;
  @observable String stateString;
  @observable DateTime eta;
  @observable String etaDatetimeString;

  BuildSlot();

  void update(Map<String, dynamic> data, Map<int, Ship> shipDefinitionMap) {
    id = data["id"];
    ship = shipDefinitionMap[data["ship_def_id"]];
    fuelSpent = data["spent_resource"]["fuel"];
    ammoSpent = data["spent_resource"]["ammo"];
    steelSpent = data["spent_resource"]["steel"];
    bauxiteSpent = data["spent_resource"]["bauxite"];
    material = data["material"];
    stateString = STATE_MAP[data["state"]];

    // ETA.
    if (data["eta"] != 0) {
      eta = new DateTime.fromMillisecondsSinceEpoch(data["eta"], isUtc: true)
        .toLocal();
      etaDatetimeString = formatShortTime(eta);
    } else {
      eta = null;
      etaDatetimeString = null;
    }
  }
}

void handleBuildDock(Assistant assistant, AssistantModel model,
                     Map<String, dynamic> data) {
  model.numShipsBeingBuilt =
      data["slots"].where((s) => s["state"] != 0).length;

  var slotsLength = data["slots"].length;
  resizeList(model.buildSlots, slotsLength, () => new BuildSlot());
  for (var i = 0; i < slotsLength; i++) {
    model.buildSlots[i].update(data["slots"][i], model.shipDefinitionMap);
  }
}