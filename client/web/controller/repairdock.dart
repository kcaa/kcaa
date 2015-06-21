part of kcaa_controller;

void handleRepairDock(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  model.numShipsBeingRepaired =
      data["slots"].where((s) => s["ship_id"] != 0).length;

  var slotsLength = data["slots"].length;
  resizeList(model.repairSlots, slotsLength, () => new RepairSlot());
  for (var i = 0; i < slotsLength; i++) {
    model.repairSlots[i].update(data["slots"][i], model.shipMap);
  }
}
