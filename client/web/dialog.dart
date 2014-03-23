library kcaa_dialog;

import 'dart:html';
import 'package:polymer/polymer.dart';

import 'assistant.dart';
import 'model/assistant.dart';

class KcaaDialog extends PolymerElement {
  // Model and the assistant element. These values are set during the
  // initialization phase of the assistant element.
  @observable AssistantModel model;
  Assistant assistant;

  KcaaDialog.created() : super.created();

  // Called when the dialog is being shown.
  void show() {}

  @observable
  void close() {
    querySelector("#modalDialogContainer").classes.remove("in");
    this.classes.add("hidden");
  }
}

@CustomTag('kcaa-schedule-dialog')
class ScheduleDialog extends KcaaDialog {
  @observable bool enabled;
  @observable List<ScheduleFragment> schedules;

  ScheduleDialog.created() : super.created();

  @override
  void show() {
    enabled = model.autoManipulatorsEnabled;
    schedules = new ObservableList.from(model.autoManipulatorSchedules);
  }

  void addSchedule() {
    schedules.add(new ScheduleFragment(0, 0));
  }

  void removeSchedule(MouseEvent e, var detail, Element target) {
    var index = int.parse(target.dataset["index"]);
    schedules.removeAt(index);
  }

  void ok() {
    assistant.setAutoManipulatorSchedules(enabled, schedules);
    close();
  }
}