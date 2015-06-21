part of kcaa_controller;

void handleShipList(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  // Reset the equipping ship info.
  for (var equipment in model.equipmentMap.values) {
    equipment.ship = null;
  }
  Set<int> presentShips = new Set<int>();
  for (var shipData in (data["ships"] as Map).values) {
    var id = shipData["id"];
    var ship = model.shipMap[id];
    if (ship == null) {
      ship = new Ship();
      model.shipMap[id] = ship;
    }
    ship.update(shipData, model.shipTypeDefinitionMap, model.fleets,
        model.equipmentMap);
    presentShips.add(id);
  }
  updateAvailableEquipments(model);
  // Remove ships that are no longer available.
  Set<int> removedShips =
      new Set<int>.from(model.shipMap.keys).difference(presentShips);
  for (var id in removedShips) {
    model.shipMap.remove(id);
  }
  reorderShipList(assistant, model);
  model.numFilteredShips =
      model.ships.where((ship) => assistant.shipList.filter(ship)).length;
  model.numDamagedShipsToWarmUp = model.ships
      .where((ship) => Ship.filterCanWarmUp(ship))
      .where((ship) => Ship.filterCanRepair(ship)).length;
  model.numShipsToWarmUp =
      model.ships.where((ship) => Ship.filterCanWarmUp(ship)).length;
  model.numShipsUnderRepair =
      model.ships.where((ship) => Ship.filterUnderRepair(ship)).length;
  model.numShipsToRepair =
      model.ships.where((ship) => Ship.filterCanRepair(ship)).length;
  updateShipTags(model);
}

void reorderShipList(Assistant assistant, AssistantModel model) {
  var shipsLength = model.shipMap.length;
  resizeList(model.ships, shipsLength, () => new Ship());
  var sortedShips = model.shipMap.values.toList(growable: false);
  var inverter = assistant.shipList.shipOrderInverter;
  var comparer = assistant.shipList.shipComparer;
  sortedShips.sort((a, b) => inverter(comparer(a, b)));
  for (var i = 0; i < shipsLength; i++) {
    var ship = sortedShips[i];
    // Update the ship list only when the order has changed.
    // Seems like it requires tremendous amount of load to assign a value to
    // ObservableList, even if the value being assigned is the same as the
    // previous value.
    if (model.ships[i] != ship) {
      model.ships[i] = ship;
    }
  }
}

void notifyShipList(AssistantModel model) {
  var shipIdsInFleets = new Set.from(
      model.fleets.expand((fleet) => fleet.ships).map((ship) => ship.id));
  for (var ship in model.ships) {
    if (shipIdsInFleets.contains(ship.id)) {
      ship.updateBelongingFleet(model.fleets);
    } else {
      ship.belongingFleet = null;
    }
  }
}

void handleShipDefinitionList(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  model.shipTypeDefinitionMap.clear();
  for (var shipTypeData in (data["ship_types"] as Map).values) {
    model.shipTypeDefinitionMap[shipTypeData["id"]] = new ShipTypeDefinition(
        shipTypeData["id"], shipTypeData["name"],
        shipTypeData["loadable_equipment_types"], shipTypeData["sort_order"]);
  }
  for (var shipData in (data["ships"] as Map).values) {
    var ship = new Ship();
    ship.id = shipData["id"];
    ship.name = shipData["name"];
    ship.shipType = model.shipTypeDefinitionMap[shipData["ship_type"]].name;
    model.shipDefinitionMap[ship.id] = ship;
  }
}
