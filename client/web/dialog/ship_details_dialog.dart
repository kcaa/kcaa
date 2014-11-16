import 'dart:html';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import '../model/assistant.dart';
import '../util.dart';

@CustomTag('kcaa-ship-details-dialog')
class ShipDetailsDialog extends KcaaDialog {
  @observable Ship ship;
  @observable List<String> tags = new ObservableList<String>();

  ShipDetailsDialog.created() : super.created();

  @override
  void show(Element target) {
    var shipId = int.parse(target.dataset["shipId"]);
    ship = model.shipMap[shipId];
    tags.clear();
    tags.addAll(ship.tags);
  }

  void deleteTag(Event e, var detail, Element target) {
    tags.removeAt(int.parse(target.dataset["index"]));
    e.preventDefault();
  }

  void addNewTag(Event e, var detail, InputElement target) {
    tags.add(target.value);
    target.value = "";
  }

  void ok() {
    ShipPrefs shipPrefs = model.preferences.shipPrefs;
    bool prefsChanged = false;
    if (tags.isEmpty) {
      if (shipPrefs.tags.containsKey(ship.id)) {
        shipPrefs.tags.remove(ship.id);
        prefsChanged = true;
      }
    } else {
      if (shipPrefs.tags[ship.id] == null ||
          !iterableEquals(ship.tags, tags)) {
        shipPrefs.tags[ship.id] = new ShipTags(tags);
        prefsChanged = true;
      }
    }
    if (prefsChanged) {
      ship.tags.clear();
      ship.tags.addAll(tags);
      assistant.savePreferences();
    }
    close();
  }
}