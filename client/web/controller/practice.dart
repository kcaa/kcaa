part of kcaa_controller;

void handlePracticeList(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  var practicesLength = data["practices"].length;
  resizeList(model.practices, practicesLength, () => new Practice());
  for (var i = 0; i < practicesLength; i++) {
    model.practices[i].update(
        data["practices"][i], model.shipTypeDefinitionMap);
  }
  model.numPracticesDone =
      model.practices.where((p) => p.resultMessage != "").length;
}
