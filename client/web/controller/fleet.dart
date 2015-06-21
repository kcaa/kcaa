part of kcaa_controller;

void handleFleetList(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  var fleetsLength = data["fleets"].length;
  if (fleetsLength != model.fleets.length) {
    // Wait for the DOM to be updated.
    runLater(0, () => assistant.updateCollapsedSections());
  }
  resizeList(model.fleets, fleetsLength, () => new Fleet());
  for (var i = 0; i < fleetsLength; i++) {
    model.fleets[i].update(data["fleets"][i], model.shipMap, model.missions);
  }
  notifyShipList(model);
  model.someFleetChargeable = model.fleets.any((f) =>
      f.ships.any((s) => s.fuel < s.fuelCapacity || s.ammo < s.ammoCapacity));
}
