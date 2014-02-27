part of kcaa;

class Fleet {
  int id;
  String name;
  List<Ship> ships = new List<Ship>();
  String undertakingMission;
  bool collapsed;

  Fleet(Map<String, dynamic> data, Map<int, Ship> shipMap,
        List<Mission> missions, {bool collapsed: null})
      : id = data["id"],
        name = data["name"] {
    for (var shipId in data["ship_ids"]) {
      var ship = shipMap[shipId];
      ships.add(ship);
      // If there is a means to notify the change in ObservableList, I would
      // update ship.belongingFleet as well...
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
  }
}

void handleFleetList(Assistant assistant, Map<String, dynamic> data) {
  if ((data["fleets"] as List).length == assistant.fleets.length) {
    for (var i = 0; i < assistant.fleets.length; ++i) {
      var fleetData = data["fleets"][i];
      assistant.fleets[i] = new Fleet(fleetData, assistant.shipMap,
          assistant.missions, collapsed: assistant.fleets[i].collapsed);
    }
  } else {
    assistant.fleets.clear();
    for (var fleetData in data["fleets"]) {
      assistant.fleets.add(new Fleet(fleetData, assistant.shipMap,
          assistant.missions));
    }
  }
  // Wait for the DOM to be updated.
  runLater(0, () => assistant.updateCollapsedSections());
}