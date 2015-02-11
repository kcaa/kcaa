part of kcaa_model;

class PlayerInfo extends Observable {
  @observable int maxShips;
  @observable int maxEquipments;

  void update(Map<String, dynamic> data) {
    maxShips = data["max_ships"];
    maxEquipments = data["max_equipments"];
  }
}

class PlayerResources extends Observable {
  @observable int fuel;
  @observable int ammo;
  @observable int steel;
  @observable int bauxite;

  void update(Map<String, dynamic> data) {
    fuel = data["fuel"];
    ammo = data["ammo"];
    steel = data["steel"];
    bauxite = data["bauxite"];
  }
}

void handlePlayerInfo(Assistant assistant, AssistantModel model,
                      Map<String, dynamic> data) {
  model.playerInfo.update(data);
}

void handlePlayerResources(Assistant assistant, AssistantModel model,
                           Map<String, dynamic> data) {
  model.resources.update(data);
}