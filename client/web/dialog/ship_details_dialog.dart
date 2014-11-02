import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';

@CustomTag('kcaa-ship-details-dialog')
class ShipDetailsDialog extends KcaaDialog {
  @observable Ship ship;

  ShipDetailsDialog.created() : super.created();

  @override
  void show(Element target) {
    var shipId = int.parse(target.dataset["shipId"]);
    ship = model.shipMap[shipId];
  }
}