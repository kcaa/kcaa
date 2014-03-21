part of kcaa;

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
      ships[i] = shipMap[data["ship_ids"][i]];
    }
    if (data["mission_id"] != null) {
      var missionId = data["mission_id"];
      for (var mission in missions) {
        if (mission.id == missionId) {
          undertakingMission = mission.name;
          break;
        }
      }
    }
    if (collapsed != null) {
      this.collapsed = collapsed;
    } else {
      this.collapsed = id != 1;
    }
    defaultClass = this.collapsed ? "hidden": "";
  }
}

void handleFleetList(Assistant assistant, Map<String, dynamic> data) {
  var fleetsLength = data["fleets"].length;
  if (assistant.fleets.length != fleetsLength) {
    if (fleetsLength < assistant.fleets.length) {
      assistant.fleets.removeRange(fleetsLength, assistant.fleets.length);
    } else {
      for (var i = assistant.fleets.length; i < fleetsLength; i++) {
        assistant.fleets.add(new Fleet());
      }
    }
    // Wait for the DOM to be updated.
    runLater(0, () => assistant.updateCollapsedSections());
  }
  for (var i = 0; i < fleetsLength; i++) {
    assistant.fleets[i].update(data["fleets"][i], assistant.shipMap,
        assistant.missions, collapsed: assistant.fleets[i].collapsed);
  }
  notifyShipList(assistant);
}