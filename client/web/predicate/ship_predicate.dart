library kcaa_predicate;

import 'dart:html';
import 'package:polymer/polymer.dart';

import '../model/assistant.dart';
import 'kselection.dart';

@CustomTag('kcaa-ship-predicate')
class ShipPredicateElement extends PolymerElement {
  @published ShipPredicate predicate;

  CustomEvent change = new CustomEvent("predicatechange");

  ShipPredicateElement.created() : super.created();

  void dispatchChange() {
    dispatchEvent(change);
  }

  void updateType(Event e, var detail, KSelectionElement target) {
    if (target.kselection.value == 'not' && predicate.not == null) {
      predicate.not = new ShipPredicate.fromTRUE();
    }
    dispatchChange();
  }

  void addOr() {
    predicate.or.add(new ShipPredicate.fromTRUE());
    dispatchChange();
  }

  void deleteOr(MouseEvent e, var detail, Element target) {
    var index = int.parse(target.dataset["index"]);
    predicate.or.removeAt(index);
    dispatchChange();
  }

  void addAnd() {
    predicate.and.add(new ShipPredicate.fromTRUE());
    dispatchChange();
  }

  void deleteAnd(MouseEvent e, var detail, Element target) {
    var index = int.parse(target.dataset["index"]);
    predicate.and.removeAt(index);
    dispatchChange();
  }
}