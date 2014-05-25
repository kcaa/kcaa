part of kcaa_model;

// Model classes in this file are basically clones of the Preferences object in
// KCAA server. Keep them in sync as much as possible.
// Unfortunately, json_object doen't work well with dart2js, which prevents
// these classes from being a simple observable object created from JSON...

class ScheduleFragment extends Observable {
  @observable int start;
  @observable int end;

  ScheduleFragment(this.start, this.end);
}

class AutomanPrefs extends Observable {
  @observable bool enabled = false;
  @observable final List<ScheduleFragment> schedules =
      new ObservableList<ScheduleFragment>();
}

class Preferences extends Observable {
  @observable AutomanPrefs automanPrefs = new AutomanPrefs();
}

void handlePreferences(Assistant assistant, AssistantModel model,
                       Map<String, dynamic> data) {
  model.preferences.automanPrefs.enabled = data["automan_prefs"]["enabled"];
  model.preferences.automanPrefs.schedules.clear();
  for (var schedule in data["automan_prefs"]["schedules"]) {
    model.preferences.automanPrefs.schedules.add(
        new ScheduleFragment(schedule["start"], schedule["end"]));
  }
}
