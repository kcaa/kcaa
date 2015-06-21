part of kcaa_controller;

void handleBuildDock(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  model.numShipsBeingBuilt = data["slots"].where((s) => s["state"] != 0).length;

  var slotsLength = data["slots"].length;
  resizeList(model.buildSlots, slotsLength, () => new BuildSlot());
  for (var i = 0; i < slotsLength; i++) {
    model.buildSlots[i].update(data["slots"][i], model.shipDefinitionMap);
  }
}
