import 'dart:html';
import 'package:polymer/polymer.dart';

import 'assistant.dart';
import 'model/assistant.dart';

@CustomTag('kcaa-shiplist')
class ShipListElement extends PolymerElement {
  @published Assistant assistant;
  @published List<Ship> ships;
  @published ShipFilterer filter = Ship.filterNone;
  @published bool fleet = false;
  @published bool disabled = false;

  ShipComparer shipComparer = Ship.compareByKancolleLevel;
  ShipOrderInverter shipOrderInverter = Ship.orderInDescending;

  ShipListElement.created() : super.created();

  String toFilterClass(bool filtered) {
    return filtered ? "" : "hidden";
  }

  @override
  void attached() {
    if (!fleet) {
      addShipSortLabels();
    }
  }

  void addShipSortLabels() {
    for (Element columnHeader in
        shadowRoot.querySelectorAll("div[data-type]")) {
      if (columnHeader.dataset.containsKey("label")) {
        continue;
      }
      var sortLabel = new AnchorElement();
      sortLabel.text = columnHeader.text;
      sortLabel.href = "#";
      sortLabel.onClick.listen(sortShips);
      columnHeader.dataset["label"] = columnHeader.text;
      columnHeader.text = "";
      columnHeader.children.add(sortLabel);
    }
  }

  void sortShips(MouseEvent e) {
    var sortLabel = e.target as Element;
    var columnHeader = sortLabel.parent;
    var type = columnHeader.dataset["type"];
    var order = columnHeader.dataset["order"];
    var label = columnHeader.dataset["label"];
    // Determine the metric to use.
    shipComparer = Ship.SHIP_COMPARER[type];
    // Determine the sort order.
    if (order != "descending") {
      shipOrderInverter = Ship.orderInDescending;
      sortLabel.text = label + "▼";
      columnHeader.dataset["order"] = "descending";
    } else {
      shipOrderInverter = Ship.orderInAscending;
      sortLabel.text = label + "▲";
      columnHeader.dataset["order"] = "ascending";
    }
    // Sort the ships using these criteria.
    ships.sort((a, b) => shipOrderInverter(shipComparer(a, b)));
    resetOtherShipSortLabels(columnHeader.parent, columnHeader);
    e.preventDefault();
  }

  void resetOtherShipSortLabels(Element row, Element target) {
    for (Element columnHeader in row.children) {
      if (columnHeader == target) {
        continue;
      }
      columnHeader.dataset.remove("order");
      var sortLabel = columnHeader.children[0];
      sortLabel.text = columnHeader.dataset["label"];
    }
  }

  void showModalDialog(MouseEvent e, var detail, Element target) {
    if (assistant != null) {
      assistant.showModalDialog(e, detail, target);
    } else {
      e.preventDefault();
    }
  }
}