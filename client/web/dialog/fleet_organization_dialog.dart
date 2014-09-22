import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';

@CustomTag('kcaa-fleet-organization-dialog')
class FleetOrganizationDialog extends KcaaDialog {
  @observable SavedFleet fleet;
  @observable List<Ship> ships;

  @observable final String defaultClass = "";
  @observable final bool ignoreFilter = true;
  @observable bool debug = false;

  FleetOrganizationDialog.created() : super.created();

  @override
  void show(Element target) {
    var fleetName = target.dataset["fleetName"];
    fleet = model.preferences.fleetPrefs.savedFleets.firstWhere(
        (savedFleet) => savedFleet.name == fleetName);
    ships = new ObservableList<Ship>.from(fleet.shipRequirements.map(
        (requirement) => model.shipMap[requirement.id]));
    debug = model.debug;
  }
}