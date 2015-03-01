library kcaa_deployedequipmentlist;

import 'dart:html';
import 'package:polymer/polymer.dart';

import '../model/assistant.dart';

class DeployedEquipmentEventDetail {
  int slot;
  Element target;

  DeployedEquipmentEventDetail(this.slot, this.target);
}

@CustomTag('kcaa-deployedequipmentlist')
class DeployedEquipmentListElement extends PolymerElement {
  @published List<Equipment> equipments;
  @published Ship ship;
  @published bool editable = false;

  DeployedEquipmentListElement.created() : super.created();

  void selectEquipment(Event e, var detail, Element target) {
    e.preventDefault();
    detail = new DeployedEquipmentEventDetail(
        int.parse(target.dataset["slot"]), target);
    dispatchEvent(new CustomEvent("equipmentselected", detail: detail));
  }

  void clearEquipment(Event e, var detail, Element target) {
    detail = new DeployedEquipmentEventDetail(
        int.parse(target.dataset["slot"]), target);
    dispatchEvent(new CustomEvent("equipmentcleared", detail: detail));
  }
}