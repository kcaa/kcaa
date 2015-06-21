part of kcaa_controller;

void handlePreferences(
    Assistant assistant, AssistantModel model, Map<String, dynamic> data) {
  Preferences prefs = new Preferences();
  prefs.automanPrefs.enabled = data["automan_prefs"]["enabled"];
  prefs.automanPrefs.schedules.clear();
  for (var schedule in data["automan_prefs"]["schedules"]) {
    prefs.automanPrefs.schedules
        .add(new ScheduleFragment(schedule["start"], schedule["end"]));
  }
  (data["ship_prefs"]["tags"] as Map).forEach((shipId, tags) =>
      prefs.shipPrefs.tags[int.parse(shipId)] = new ShipTags(tags["tags"]));
  for (var savedFleet in data["fleet_prefs"]["saved_fleets"]) {
    prefs.fleetPrefs.savedFleets.add(new FleetDeployment.fromJSON(savedFleet));
  }
  for (var savedFleet in data["fleet_prefs"]["saved_combined_fleets"]) {
    prefs.fleetPrefs.savedCombinedFleets
        .add(new CombinedFleetDeployment.fromJSON(savedFleet));
  }
  for (var deployment in data["equipment_prefs"]["deployments"]) {
    prefs.equipmentPrefs.deployments
        .add(new EquipmentGeneralDeployment.fromJSON(deployment));
  }
  for (var practicePlan in data["practice_prefs"]["practice_plans"]) {
    PracticePlan practicePlanObject = new PracticePlan(
        practicePlan["opponent_fleet_type"], practicePlan["fleet_name"],
        practicePlan["formation"]);
    prefs.practicePrefs.practicePlans.add(practicePlanObject);
  }
  for (var missionPlan in data["mission_prefs"]["mission_plans"]) {
    MissionPlan missionPlanObject = new MissionPlan(missionPlan["fleet_id"],
        missionPlan["mission_id"], missionPlan["fleet_name"],
        missionPlan["enabled"]);
    prefs.missionPrefs.missionPlans.add(missionPlanObject);
  }
  model.preferences = prefs;
}
