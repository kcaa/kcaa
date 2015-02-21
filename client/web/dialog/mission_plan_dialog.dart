import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';
import '../util.dart';

class FriendlyMissionPlan extends Observable {
  @observable int fleetId;
  @observable KSelection mission = new KSelection();
  @observable KSelection fleetName = new KSelection();
  @observable bool enabled;

  FriendlyMissionPlan(MissionPlan plan, List<Mission> missions,
      List<FleetDeployment> fleetDeployments) {
    fleetId = plan.fleetId;
    mission.updateCandidates(missions.map((mission) =>
        [mission.id.toString(), mission.name]));
    mission.value = plan.missionId.toString();
    fleetName.updateCandidates(fleetDeployments.map((fleetDeployment) =>
        fleetDeployment.name));
    fleetName.value = plan.fleetName;
    enabled = plan.enabled;
  }

  MissionPlan toMissionPlan() {
    return new MissionPlan(fleetId, int.parse(mission.value), fleetName.value,
        enabled);
  }
}

@CustomTag('kcaa-mission-plan-dialog')
class MissionPlanDialog extends KcaaDialog {
  @observable List<FriendlyMissionPlan> missionPlans =
      new ObservableList<FriendlyMissionPlan>();

  MissionPlanDialog.created() : super.created();

  @override
  void show(Element target) {
    missionPlans.clear();
    missionPlans.addAll(model.preferences.missionPrefs.missionPlans.map(
        (plan) => new FriendlyMissionPlan(plan, model.missions,
            model.preferences.fleetPrefs.savedFleets)));
  }

  void ok() {
    model.preferences.missionPrefs.missionPlans.clear();
    model.preferences.missionPrefs.missionPlans.addAll(missionPlans.map(
        (plan) => plan.toMissionPlan()));
    assistant.savePreferences();
    close();
  }
}