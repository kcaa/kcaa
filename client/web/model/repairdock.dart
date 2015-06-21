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
    } else {
      ship = null;
    }

    // ETA.
    if (data["eta"] != 0) {
      eta = new DateTime.fromMillisecondsSinceEpoch(data["eta"], isUtc: true)
          .toLocal();
      etaDatetimeString = formatShortTime(eta);
    } else {
      eta = null;
      etaDatetimeString = null;
    }
  }
}
