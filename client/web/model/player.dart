part of kcaa_model;

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
void handlePlayerResources(Assistant assistant, AssistantModel model,
                           Map<String, dynamic> data) {
  model.resources.update(data);
}