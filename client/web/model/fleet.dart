part of kcaa_model;

class Fleet extends Observable {
  @observable int id;
  @observable String name;
  // Somehow this list needs to be @observable for getting ships.length.
  @observable final List<Ship> ships = new ObservableList<Ship>();
  @observable String undertakingMission;
  @observable bool collapsed = null;
  @observable String defaultClass;

  Fleet();

  void update(Map<String, dynamic> data, Map<int, Ship> shipMap,
        List<Mission> missions, {bool collapsed: null}) {
    id = data["id"];
    name = data["name"];

    var shipsLength = data["ship_ids"].length;
    if (ships.length != shipsLength) {
      if (shipsLength < ships.length) {
        ships.removeRange(shipsLength, ships.length);
      } else {
        for (var i = ships.length; i < shipsLength; i++) {
          ships.add(null);
        }
      }
    }
    for (var i = 0; i < shipsLength; i++) {
      var ship = shipMap[data["ship_ids"][i]];
      // Do not update the ObservableList if the value is the same.
      if (ships[i] != ship) {
        ships[i] = ship;
      }
    }
    if (data["mission_id"] != null) {
      undertakingMission = "不明";
      var missionId = data["mission_id"];
      for (var mission in missions) {
        if (mission.id == missionId) {
          undertakingMission = mission.name;
          break;
        }
      }
    } else {
      undertakingMission = null;
    }
    if (collapsed != null) {
      this.collapsed = collapsed;
    } else {
      this.collapsed = id != 1;
    }
    defaultClass = this.collapsed ? "hidden": "";
  }
}

void handleFleetList(Assistant assistant, AssistantModel model,
                     Map<String, dynamic> data) {
  var fleetsLength = data["fleets"].length;
  if (fleetsLength != model.fleets.length) {
    // Wait for the DOM to be updated.
    runLater(0, () => assistant.updateCollapsedSections());
  }
  resizeList(model.fleets, fleetsLength, () => new Fleet());
  for (var i = 0; i < fleetsLength; i++) {
    model.fleets[i].update(data["fleets"][i], model.shipMap,
        model.missions, collapsed: model.fleets[i].collapsed);
  }
  notifyShipList(model);
}