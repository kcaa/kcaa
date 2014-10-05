part of kcaa_model;

class BuildSlot extends Observable {
  @observable int id;
  @observable DateTime eta;
  @observable String etaDatetimeString;

  BuildSlot();
}

void handleBuildDock(Assistant assistant, AssistantModel model,
                     Map<String, dynamic> data) {
  // TODO: Implement.
  model.numShipsBeingBuilt = 0;
}