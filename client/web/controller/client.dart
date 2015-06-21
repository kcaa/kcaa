part of kcaa_controller;

void handleScreen(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  model.screen = ClientScreen.SCREEN_MAP[data["screen"]];
}

void handleRunningManipulators(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  model.runningManipulator = data["running_manipulator"];
  model.manipulatorsInQueue.clear();
  model.manipulatorsInQueue.addAll(data["manipulators_in_queue"]);
  model.autoManipulatorsActive = data["auto_manipulators_active"];

  // Change the document title if there is a running manipulator.
  var title = querySelector("title") as TitleElement;
  if (model.runningManipulator != null) {
    title.text = "${model.runningManipulator} - ${title.title}";
  } else {
    title.text = title.title;
  }
}
