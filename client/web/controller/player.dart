part of kcaa_controller;

void handlePlayerInfo(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  model.playerInfo.update(data);
}

void handlePlayerResources(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  model.resources.update(data);
}
