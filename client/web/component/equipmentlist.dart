import 'dart:html';
import 'package:polymer/polymer.dart';

import '../assistant.dart';
import '../model/assistant.dart';

@CustomTag('kcaa-equipmentlist')
class EquipmentListElement extends PolymerElement {
  @published Assistant assistant;
  @published List<EquipmentDefinition> definitions;

  EquipmentListElement.created() : super.created();

  void showModalDialog(MouseEvent e, var detail, Element target) {
    if (assistant != null) {
      assistant.showModalDialog(e, detail, target);
    } else {
      e.preventDefault();
    }
  }
}