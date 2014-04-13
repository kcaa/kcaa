part of kcaa_model;

class RepairSlot extends Observable {
  @observable int id;
  @observable Ship ship;
  @observable DateTime eta;
  @observable String etaDatetimeString;

  RepairSlot();

  void update(Map<String, dynamic> data, Map<int, Ship> shipMap) {
    id = data["id"];
    if (data["ship_id"] != 0) {
      ship = shipMap[data["ship_id"]];
    }

    // ETA.
    if (data["eta"] != 0) {
      eta = new DateTime.fromMillisecondsSinceEpoch(data["eta"], isUtc: true)
        .toLocal();
      etaDatetimeString = formatShortTime(eta);
    }
  }
}

void handleRepairDock(Assistant assistant, AssistantModel model,
                      Map<String, dynamic> data) {
  model.numShipsBeingRepaired =
      data["slots"].where((s) => s["ship_id"] != 0).length;

  var slotsLength = data["slots"].length;
  resizeList(model.repairSlots, slotsLength, () => new RepairSlot());
  for (var i = 0; i < slotsLength; i++) {
    model.repairSlots[i].update(data["slots"][i], model.shipMap);
  }
}