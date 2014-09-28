import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';

class FriendlyPracticePlan extends PracticePlan {
  @observable String opponentFleetTypeName;
  @observable String formationName;

  @observable List<FleetDeployment> savedFleets =
      new ObservableList<FleetDeployment>();
  @observable List<String> formationNames =
      new ObservableList<String>();

  FriendlyPracticePlan(PracticePlan p, AssistantModel model)
      : super(p.opponentFleetType, p.fleetName, p.formation) {
    opponentFleetTypeName = Practice.FLEET_TYPE[opponentFleetType];
    formationName = Practice.FORMATION_NAME[formation];

    savedFleets.addAll(model.preferences.fleetPrefs.savedFleets);
    var formations = Practice.FORMATION_NAME.keys.toList();
    formations.sort();
    formationNames = formations.map((f) => Practice.FORMATION_NAME[f]);
  }

  PracticePlan toPracticePlan() {
    return new PracticePlan(opponentFleetType, fleetName,
        Practice.FORMATION_NAME_REVERSE[formationName]);
  }
}

@CustomTag('kcaa-practice-plan-dialog')
class PracticePlanDialog extends KcaaDialog {
  @observable List<FriendlyPracticePlan> practicePlans =
      new ObservableList<FriendlyPracticePlan>();

  PracticePlanDialog.created() : super.created();

  @override
  void show(Element target) {
    practicePlans.clear();
    practicePlans.addAll(model.preferences.practicePrefs.practicePlans.map((p) {
      return new FriendlyPracticePlan(p, model);
    }));
  }

  void ok() {
    model.preferences.practicePrefs.practicePlans.clear();
    model.preferences.practicePrefs.practicePlans.addAll(practicePlans.map((p) {
      return p.toPracticePlan();
    }));
    assistant.savePreferences();
    close();
  }
}