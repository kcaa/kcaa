part of kcaa;

class Fleet {
  int id;
  String name;
  List<Ship> ships = new List<Ship>();
  String undertakingMission;

  Fleet(Map<String, dynamic> data, Map<int, Ship> shipMap,
        List<Mission> missions)
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
  }
}

void handleFleetList(Assistant assistant, Map<String, dynamic> data) {
  assistant.fleets.clear();
  for (var fleetData in data["fleets"]) {
    assistant.fleets.add(new Fleet(fleetData, assistant.shipMap,
        assistant.missions));
  }
}