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

@CustomTag('eplusx-kancolle-assistant')
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
  static final List<String> REFERENCED_OBJECTS = <String>["ShipList"];

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

    availableObjectsChecker =
        new Timer.periodic(MILLISECOND * 100, (Timer timer) {
      updateAvailableObjects();
    });
    addCollapseButtons();
    handleObjects(serverGetObjects);
  }

  void collapseSection(Element header, bool toCollapse,
                       [Element collapseButton=null]) {
    for (var element in header.parent.children) {
      if (element == header) {
        continue;
      }
      element.classes.toggle("hidden", toCollapse);
    }
    header.dataset["collapsed"] = (toCollapse).toString();
    if (collapseButton != null) {
      collapseButton.text = toCollapse ? "►" : "▼";
    }
  }

  void addCollapseButtons() {
    // shadowRoot provides access to the root of this custom element.
    for (Element header in shadowRoot.querySelectorAll("div.board > h3")) {
      var collapseButton = new ButtonElement();
      collapseButton.classes.add("collapse");
      collapseButton.onClick.listen((MouseEvent e) {
        var toCollapse = header.dataset["collapsed"] == "false";
        collapseSection(header, toCollapse, collapseButton);
      });
      header.children.add(collapseButton);
      collapseSection(header, header.dataset["collapsed"] == "true",
          collapseButton);
    }
  }

  Future handleObject(String objectType) {
    var handler = OBJECT_HANDLERS[objectType];
    if (handler != null) {
      return getObject(objectType, false).then((Map<String, dynamic> data) {
        handler(this, data);
      });
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
}