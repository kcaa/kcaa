import 'dart:html';
import 'package:polymer/polymer.dart';

import '../util.dart';

@CustomTag('kcaa-kselection')
class KSelectionElement extends PolymerElement {
  @published KSelection kselection;

  CustomEvent change = new CustomEvent("selectionchange");

  KSelectionElement.created() : super.created();

  void dispatchChange() {
    dispatchEvent(change);
  }
}