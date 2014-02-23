library kcaa;

import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';
import 'package:polymer/polymer.dart';

part 'domain/missionlist.dart';
part 'domain/questlist.dart';
part 'domain/screen.dart';
part 'domain/ship.dart';
part 'util.dart';

@CustomTag('eplusx-kancolle-assistant')
class Assistant extends PolymerElement {
  // Ships.
  final List<Ship> ships = new ObservableList<Ship>();

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
  final Map<String, Function> OBJECT_HANDLERS = <String, Function>{
    "MissionList": handleMissionList,
    "QuestList": handleQuestList,
    "Screen": handleScreen,
    "ShipList": handleShipList,
  };

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

  void addCollapseButtons() {
    // shadowRoot provides access to the root of this custom element.
    for (Element header in shadowRoot.querySelectorAll("div.board > h3")) {
      var collapseButton = new ButtonElement();
      collapseButton.classes.add("collapse");
      collapseButton.text = "▼";
      collapseButton.dataset["collapsed"] = "false";
      collapseButton.onClick.listen((MouseEvent e) {
        var toCollapse = collapseButton.dataset["collapsed"] == "false";
        for (var element in header.parent.children) {
          if (element == header) {
            continue;
          }
          element.classes.toggle("hidden", toCollapse);
        }
        collapseButton.text = toCollapse ? "►" : "▼";
        collapseButton.dataset["collapsed"] = (toCollapse).toString();
      });
      header.children.add(collapseButton);
    }
  }

  void handleObjects(Uri objectsUri) {
    HttpRequest.getString(objectsUri.toString())
      .then((String content) {
        List<String> objectTypes = JSON.decode(content);
        for (var objectType in objectTypes) {
          var handler = OBJECT_HANDLERS[objectType];
          if (handler != null) {
            getObject(objectType, false).then((Map<String, dynamic> data) {
              handler(this, data);
            });
          }
        }
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