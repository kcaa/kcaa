import 'dart:html';
import 'package:polymer/polymer.dart';

import '../model/assistant.dart';
import 'kselection.dart';

@CustomTag('kcaa-equipment-predicate')
class EquipmentPredicateElement extends PolymerElement {
  @published EquipmentPredicate predicate;

  CustomEvent change = new CustomEvent("predicatechange");

  EquipmentPredicateElement.created() : super.created();

  void dispatchChange() {
    dispatchEvent(change);
  }

  void updateType(Event e, var detail, KSelectionElement target) {
    if (target.kselection.value == 'not' && predicate.not == null) {
      predicate.not = new EquipmentPredicate.fromTRUE();
    }
    dispatchChange();
  }

  void addOr() {
    predicate.or.add(new EquipmentPredicate.fromTRUE());
    dispatchChange();
  }

  void deleteOr(MouseEvent e, var detail, Element target) {
    var index = int.parse(target.dataset["index"]);
    predicate.or.removeAt(index);
    dispatchChange();
  }

  void addAnd() {
    predicate.and.add(new EquipmentPredicate.fromTRUE());
    dispatchChange();
  }

  void deleteAnd(MouseEvent e, var detail, Element target) {
    var index = int.parse(target.dataset["index"]);
    predicate.and.removeAt(index);
    dispatchChange();
  }
}