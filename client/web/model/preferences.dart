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

class ShipTags extends Observable {
  @observable final List<String> tags = new ObservableList<String>();

  ShipTags(List<String> tags) {
    this.tags.addAll(tags);
  }
}

class ShipPrefs extends Observable {
  @observable Map<int, ShipTags> tags = new ObservableMap<int, ShipTags>();
}

class FleetPrefs extends Observable {
  @observable final List<FleetDeployment> savedFleets =
      new ObservableList<FleetDeployment>();
}

class PracticePlan extends Observable {
  @observable int opponentFleetType;
  @observable String fleetName;
  @observable int formation;

  PracticePlan(this.opponentFleetType, this.fleetName, this.formation);
}

class PracticePrefs extends Observable {
  @observable final List<PracticePlan> practicePlans =
      new ObservableList<PracticePlan>();
}

class MissionPlan extends Observable {
  @observable int fleetId;
  @observable int missionId;
  @observable String fleetName;

  MissionPlan(this.fleetId, this.missionId, this.fleetName);
}

class MissionPrefs extends Observable {
  @observable final List<MissionPlan> missionPlans =
      new ObservableList<MissionPlan>();
}

class Preferences extends Observable {
  @observable AutomanPrefs automanPrefs = new AutomanPrefs();
  @observable ShipPrefs shipPrefs = new ShipPrefs();
  @observable FleetPrefs fleetPrefs = new FleetPrefs();
  @observable PracticePrefs practicePrefs = new PracticePrefs();
  @observable MissionPrefs missionPrefs = new MissionPrefs();

  // Convert this preferences object to JSON so that the server can directly
  // accept it as the Prefenreces object.
  String toJSON() {
    return JSON.encode({
      "automan_prefs": {
        "enabled": automanPrefs.enabled,
        "schedules": automanPrefs.schedules.map((scheduleFragment) => {
          "start": scheduleFragment.start,
          "end": scheduleFragment.end,
        }).toList(),
      },
      "ship_prefs": {
        "tags": new Map<String, dynamic>.fromIterable(shipPrefs.tags.keys,
            key: (key) => key.toString(),
            value: (key) => {
              "tags": shipPrefs.tags[key].tags,
            }),
      },
      "fleet_prefs": {
        "saved_fleets": fleetPrefs.savedFleets.map((savedFleet) =>
            savedFleet.toJSONEncodable()).toList(),
      },
      "practice_prefs": {
        "practice_plans": practicePrefs.practicePlans.map((practicePlan) => {
          "opponent_fleet_type": practicePlan.opponentFleetType,
          "fleet_name": practicePlan.fleetName,
          "formation": practicePlan.formation,
        }).toList(),
      },
      "mission_prefs": {
        "mission_plans": missionPrefs.missionPlans.map((missionPlan) => {
          "fleet_id": missionPlan.fleetId,
          "mission_id": missionPlan.missionId,
          "fleet_name": missionPlan.fleetName,
        }).toList(),
      },
    });
  }
}

void handlePreferences(Assistant assistant, AssistantModel model,
                       Map<String, dynamic> data) {
  Preferences prefs = new Preferences();
  prefs.automanPrefs.enabled = data["automan_prefs"]["enabled"];
  prefs.automanPrefs.schedules.clear();
  for (var schedule in data["automan_prefs"]["schedules"]) {
    prefs.automanPrefs.schedules.add(
        new ScheduleFragment(schedule["start"], schedule["end"]));
  }
  (data["ship_prefs"]["tags"] as Map).forEach((shipId, tags) =>
      prefs.shipPrefs.tags[int.parse(shipId)] = new ShipTags(tags["tags"]));
  for (var savedFleet in data["fleet_prefs"]["saved_fleets"]) {
    prefs.fleetPrefs.savedFleets.add(new FleetDeployment.fromJSON(savedFleet));
  }
  for (var practicePlan in data["practice_prefs"]["practice_plans"]) {
    PracticePlan practicePlanObject = new PracticePlan(
        practicePlan["opponent_fleet_type"],
        practicePlan["fleet_name"],
        practicePlan["formation"]);
    prefs.practicePrefs.practicePlans.add(practicePlanObject);
  }
  for (var missionPlan in data["mission_prefs"]["mission_plans"]) {
    MissionPlan missionPlanObject = new MissionPlan(
        missionPlan["fleet_id"],
        missionPlan["mission_id"],
        missionPlan["fleet_name"]);
    prefs.missionPrefs.missionPlans.add(missionPlanObject);
  }
  model.preferences = prefs;
}
