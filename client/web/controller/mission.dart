part of kcaa_controller;

void handleMissionList(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  var missionsLength = data["missions"].where((m) => m["name"] != null).length;
  resizeList(model.missions, missionsLength, () => new Mission());
  for (var i = 0; i < missionsLength; i++) {
    model.missions[i].update(data["missions"][i]);
  }
}
