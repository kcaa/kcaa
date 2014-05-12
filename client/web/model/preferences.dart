part of kcaa_model;

void handlePreferences(Assistant assistant, AssistantModel model,
                       JsonObject data) {
  model.autoManipulatorsEnabled = data.automan_prefs.enabled;
  model.autoManipulatorSchedules.clear();
  for (var schedule in data.automan_prefs.schedules) {
    model.autoManipulatorSchedules.add(
        new ScheduleFragment(schedule.start, schedule.end));
  }
}