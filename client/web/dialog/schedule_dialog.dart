import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';

class FriendlyScheduleFragment extends Observable {
  @observable String start;
  @observable String end;

  FriendlyScheduleFragment.empty() {
    start = "0:00";
    end = "24:00";
  }

  FriendlyScheduleFragment(ScheduleFragment fragment) {
    var startHour = fragment.start ~/ 3600;
    var startMin = (fragment.start - 3600 * startHour) ~/ 60;
    var startMinPadding = startMin < 10 ? "0" : "";
    start = "${startHour}:${startMinPadding}${startMin}";
    var endHour = fragment.end ~/ 3600;
    var endMin = (fragment.end - 3600 * endHour) ~/ 60;
    var endMinPadding = endMin < 10 ? "0" : "";
    end = "${endHour}:${endMinPadding}${endMin}";
  }

  ScheduleFragment toScheduleFragment() {
    var startComponents = start.split(":");
    var endComponents = end.split(":");
    if (startComponents.length != 2 || endComponents.length != 2) {
      throw new FormatException("Schedule fragments must have 2 components");
    }
    var startHour = int.parse(startComponents[0]);
    var startMin = int.parse(startComponents[1]);
    var endHour = int.parse(endComponents[0]);
    var endMin = int.parse(endComponents[1]);
    if (startHour < 0 || startMin < 0 || startMin >= 60 ||
        endHour < 0 || endMin < 0 || endMin >= 60) {
      throw new FormatException("Invalid range for hour:minute components");
    }
    return new ScheduleFragment(3600 * startHour + 60 * startMin,
        3600 * endHour + 60 * endMin);
  }
}

@CustomTag('kcaa-schedule-dialog')
class ScheduleDialog extends KcaaDialog {
  @observable bool enabled;
  @observable List<FriendlyScheduleFragment> schedules =
      new ObservableList();
  @observable String errorMessage;

  ScheduleDialog.created() : super.created();

  @override
  void show(Element target) {
    enabled = model.preferences.automanPrefs.enabled;
    schedules.clear();
    schedules.addAll(model.preferences.automanPrefs.schedules.map(
        (fragment) => new FriendlyScheduleFragment(fragment)));
    errorMessage = null;
  }

  void addSchedule() {
    schedules.add(new FriendlyScheduleFragment.empty());
  }

  void removeSchedule(MouseEvent e, var detail, Element target) {
    var index = int.parse(target.dataset["index"]);
    schedules.removeAt(index);
  }

  void validateSchedule(Event e, var detail, Element target) {
    try {
      var dummy = new FriendlyScheduleFragment.empty();
      dummy.start = (target as InputElement).value;
      dummy.toScheduleFragment();
      target.classes.remove("invalid");
    } on FormatException {
      target.classes.add("invalid");
    }
  }

  void ok() {
    try {
      assistant.setAutoManipulatorSchedules(enabled, schedules.map(
          (fragment) => fragment.toScheduleFragment()));
      close();
    } on FormatException {
      errorMessage = "時刻指定に誤りがあります。";
    }
  }
}
