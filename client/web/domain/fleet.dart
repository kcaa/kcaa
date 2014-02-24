part of kcaa;

class Fleet {
  int id;
  String name;
  List<Ship> ships = new List<Ship>();

  Fleet(Map<String, dynamic> data, Map<int, Ship> shipMap)
      : id = data["id"],
        name = data["name"] {
    for (var shipId in data["ship_ids"]) {
      var ship = shipMap[shipId];
      ships.add(ship);
      // If there is a means to notify the change in ObservableList, I would
      // update ship.belongingFleet as well...
    }
  }
}

void handleFleetList(Assistant assistant, Map<String, dynamic> data) {
  assistant.fleets.clear();
  for (var fleetData in data["fleets"]) {
    assistant.fleets.add(new Fleet(fleetData, assistant.shipMap));
  }
}