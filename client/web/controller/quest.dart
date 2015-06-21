part of kcaa_controller;

void handleQuestList(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  model.numQuests = data["count"];
  model.numQuestsUndertaken = data["count_undertaken"];
  var questsLength = data["quests"].length;
  if (model.quests.length != questsLength) {
    if (questsLength < model.quests.length) {
      model.quests.removeRange(questsLength, model.quests.length);
    } else {
      for (var i = model.quests.length; i < questsLength; i++) {
        model.quests.add(new Quest());
      }
    }
  }
  for (var i = 0; i < questsLength; i++) {
    model.quests[i].update(data["quests"][i]);
  }
}
