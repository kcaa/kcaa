library kcaa;

import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';
import 'package:polymer/polymer.dart';

part 'domain/fleet.dart';
part 'domain/missionlist.dart';
part 'domain/questlist.dart';
part 'domain/screen.dart';
part 'domain/ship.dart';
part 'util.dart';

class CollapsedSectionInfo {
  Element header;
  Element collapseButton;
  bool collapsed;

  CollapsedSectionInfo(this.header, this.collapseButton, this.collapsed);
}

@CustomTag('kcaa-assistant')
class Assistant extends PolymerElement {
  // Ships.
  final List<Ship> ships = new ObservableList<Ship>();
  Map<int, Ship> shipMap = new Map<int, Ship>();

  // Fleets.
  final List<Fleet> fleets = new ObservableList<Fleet>();

  // Quests.
  @observable int numQuests = 0;
  @observable int numQuestsUndertaken = 0;
  final List<Quest> quests = new ObservableList<Quest>();

  // Missions.
  final List<Mission> missions = new ObservableList<Mission>();

  // Server URIs.
  Uri clientRoot;
  Uri serverRoot;
  Uri serverGetObjects;
  Uri serverGetNewObjects;
  Uri serverGetObject;
  Uri serverReloadKCSAPIModules;
  Uri serverReloadManipulatorModules;
  Uri serverManipulate;

  // Client status.
  @observable String screen;

  // Debug information.
  @observable String debugInfo;
  final List<String> availableObjects = new ObservableList<String>();
  Set<String> availableObjectSet = new Set<String>();
  Timer availableObjectsChecker;

  // Object handlers.
  static final Map<String, Function> OBJECT_HANDLERS = <String, Function>{
    "FleetList": handleFleetList,
    "MissionList": handleMissionList,
    "QuestList": handleQuestList,
    "Screen": handleScreen,
    "ShipList": handleShipList,
  };
  // Referenced objects. If the object list contains these object types, the
  // client processes them first so that other object handlers can reference the
  // contents of them.
  static final List<String> REFERENCED_OBJECTS = <String>[
      "ShipList", "MissionList",
  ];

  Assistant.created() : super.created() {
    // Theoretically this is not safe, as some data requiring ja_JP date format
    // may run before loading completes, but that would never happen in reality.
    initializeDateFormatting("ja_JP", null).then((_) => null);
  }

  @override
  void enteredView() {
    clientRoot = Uri.parse(window.location.href);
    serverRoot = clientRoot.resolve("/");
    serverGetObjects = serverRoot.resolve("get_objects");
    serverGetNewObjects = serverRoot.resolve("get_new_objects");
    serverGetObject = serverRoot.resolve("get_object");
    serverReloadKCSAPIModules = serverRoot.resolve("reload_kcsapi");
    serverReloadManipulatorModules = serverRoot.resolve("reload_manipulators");
    serverManipulate = serverRoot.resolve("manipulate");

    availableObjectsChecker =
        new Timer.periodic(MILLISECOND * 100, (Timer timer) {
      updateAvailableObjects();
    });
    addCollapseButtons();
    updateCollapsedSections();
    handleObjects(serverGetObjects);
  }

  CollapsedSectionInfo collapseSection(Element header, Element collapseButton,
                       bool collapsed) {
    for (var element in header.parent.children) {
      if (element == header) {
        continue;
      }
      element.classes.toggle("hidden", collapsed);
    }
    header.dataset["collapsed"] = (collapsed).toString();
    collapseButton.text = collapsed ? "►" : "▼";
    return new CollapsedSectionInfo(header, collapseButton, collapsed);
  }

  CollapsedSectionInfo toggleCollapseSection(MouseEvent e) {
    var collapseButton = e.target;
    var header = collapseButton.parent;
    var collapsed = header.dataset["collapsed"] != "true";
    return collapseSection(header, collapseButton, collapsed);
  }

  void toggleCollapseFleet(MouseEvent e) {
    var collapsedSection = toggleCollapseSection(e);
    var fleetId = int.parse(collapsedSection.collapseButton.dataset["fleetId"]);
    fleets[fleetId - 1].collapsed = collapsedSection.collapsed;
  }

  void addCollapseButtons() {
    // shadowRoot provides access to the root of this custom element.
    for (Element header in
        shadowRoot.querySelectorAll("div.board *[data-collapsed]")) {
      var collapseButton = new ButtonElement();
      collapseButton.classes.add("collapse");
      collapseButton.onClick.listen(toggleCollapseSection);
      header.children.add(collapseButton);
    }
  }

  void updateCollapsedSections() {
    for (Element header in
        shadowRoot.querySelectorAll("div.board *[data-collapsed]")) {
      var collapseButton = header.querySelector("button.collapse");
      collapseSection(header, collapseButton,
          header.dataset["collapsed"] == "true");
    }
  }

  Future handleObject(String objectType) {
    var handler = OBJECT_HANDLERS[objectType];
    if (handler != null) {
      return getObject(objectType, false).then((Map<String, dynamic> data) {
        handler(this, data);
      });
    } else {
      return new Future.value(null);
    }
  }

  void handleObjects(Uri objectsUri) {
    HttpRequest.getString(objectsUri.toString())
      .then((String content) {
        Set<String> objectTypes =
            (JSON.decode(content) as List<String>).toSet();
        // Handle referenced objects first.
        Future handlerChain = new Future.value();
        for (var referencedObject in REFERENCED_OBJECTS) {
          if (objectTypes.contains(referencedObject)) {
            handlerChain = handlerChain.then((_) {
              return handleObject(referencedObject);
            });
            objectTypes.remove(referencedObject);
          }
        }
        // Then handle the rest.
        handlerChain.then((_) {
          for (var objectType in objectTypes) {
            handleObject(objectType);
          }
        });
      });
  }

  void updateAvailableObjects() {
    HttpRequest.getString(serverGetObjects.toString())
      .then((String content) {
        List<String> objectTypes = JSON.decode(content);
        var newObjectFound = false;
        for (var objectType in objectTypes) {
          newObjectFound =
              availableObjectSet.add(objectType) || newObjectFound;
        }
        if (newObjectFound) {
          availableObjects.clear();
          availableObjects.addAll(objectTypes);
        }
      });

    handleObjects(serverGetNewObjects);
  }

  void reloadKCSAPIModules() {
    HttpRequest.getString(serverReloadKCSAPIModules.toString());
  }

  void reloadManipulatorModules() {
    HttpRequest.getString(serverReloadManipulatorModules.toString());
  }

  Future<Map<String, dynamic>> getObject(String type, bool debug) {
    Uri request = serverGetObject.resolveUri(new Uri(queryParameters: {
      "type": type,
    }));
    return HttpRequest.getString(request.toString())
        .then((String content) {
          var json = JSON.decode(content);
          if (debug) {
            debugInfo = formatJson(json);
          }
          return json;
        });
  }

  void getObjectFromName(Event e, var detail, Element target) {
    getObject(target.text, true);
  }

  void goOnMission(MouseEvent e) {
    var button = e.target as HtmlElement;
    var fleetId = button.dataset["fleetId"];
    var missionId = button.dataset["missionId"];
    Uri request = serverManipulate.resolveUri(new Uri(queryParameters: {
      "type": "GoOnMission",
      "fleet_id": fleetId,
      "mission_id": missionId,
    }));
    HttpRequest.getString(request.toString());
  }
}