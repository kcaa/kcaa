import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'package:bootjack/bootjack.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:polymer/polymer.dart';

import 'dialog.dart';
import 'model/assistant.dart';
import 'util.dart';

class CollapsedSectionInfo {
  Element header;
  Element collapseButton;
  bool collapsed;

  CollapsedSectionInfo(this.header, this.collapseButton, this.collapsed);
}

@CustomTag('kcaa-assistant')
class Assistant extends PolymerElement {
  static const int SCREEN_UPDATE_INTERVAL = 1000;

  @observable AssistantModel model = new AssistantModel();

  // Server URIs.
  Uri clientRoot;
  Uri serverRoot;
  Uri serverGetObjects;
  Uri serverGetNewObjects;
  Uri serverGetObject;
  Uri serverReloadKCSAPIModules;
  Uri serverReloadManipulatorModules;
  Uri serverManipulate;
  Uri serverSetAutoManipulatorSchedules;
  Uri serverTakeScreenshot;
  Uri serverClick;

  // Debug information.
  @observable String debugInfo;
  final List<String> availableObjects = new ObservableList<String>();
  Set<String> availableObjectSet = new Set<String>();
  Timer availableObjectsChecker;
  int updateAvailableObjectsIntervalMs;
  @observable bool updateScreenPeriodically = false;

  // Object handlers.
  static final Map<String, Function> OBJECT_HANDLERS = <String, Function>{
    "FleetList": handleFleetList,
    "MissionList": handleMissionList,
    "QuestList": handleQuestList,
    "RunningManipulators": handleRunningManipulators,
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
    Modal.use();
  }

  @override
  void enteredView() {
    clientRoot = Uri.parse(window.location.href);
    var interval = clientRoot.queryParameters["interval"];
    interval = interval != null ? double.parse(interval) : 1.0;
    updateAvailableObjectsIntervalMs = (1000 * interval).toInt();
    serverRoot = clientRoot.resolve("/");
    serverGetObjects = serverRoot.resolve("get_objects");
    serverGetNewObjects = serverRoot.resolve("get_new_objects");
    serverGetObject = serverRoot.resolve("get_object");
    serverReloadKCSAPIModules = serverRoot.resolve("reload_kcsapi");
    serverReloadManipulatorModules = serverRoot.resolve("reload_manipulators");
    serverManipulate = serverRoot.resolve("manipulate");
    serverSetAutoManipulatorSchedules =
        serverRoot.resolve("set_auto_manipulator_schedules");
    serverTakeScreenshot = serverRoot.resolve("take_screenshot");
    serverClick = serverRoot.resolve("click");

    runLater(updateAvailableObjectsIntervalMs,
        updateAvailableObjectsPeriodically);
    addCollapseButtons();
    updateCollapsedSections();
    handleObjects(serverGetObjects);
    // TODO: Ensure this happens after all other dialog elements are
    // initialized.
    runLater(1000, () => passModelToDialogs());
    runLater(3000, () => reloadScreenshot());
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
    model.fleets[fleetId - 1].collapsed = collapsedSection.collapsed;
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
        handler(this, model, data);
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

  void updateAvailableObjectsPeriodically() {
    updateAvailableObjects();
    runLater(updateAvailableObjectsIntervalMs,
        updateAvailableObjectsPeriodically);
  }

  void reloadKCSAPIModules() {
    HttpRequest.getString(serverReloadKCSAPIModules.toString());
  }

  void reloadManipulatorModules() {
    HttpRequest.getString(serverReloadManipulatorModules.toString());
  }

  Future<Map<String, dynamic>> getObject(String type, bool debug) {
    var request = serverGetObject.resolveUri(new Uri(queryParameters: {
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

  void passModelToDialogs() {
    var dialogContainer = querySelector("#kcaaDialogContainer");
    for (var dialog in dialogContainer.children) {
      try {
        dialog.model = model;
        dialog.assistant = this;
        dialog.name = dialog.toString();
      } on Error {
        // Simply ignore non-dialog elements.
      }
    }
  }

  void reloadScreenshot() {
    ($["screenshot"] as ImageElement).src = serverTakeScreenshot.resolveUri(
        new Uri(queryParameters: {
          "format": "jpeg",
          "quality": "50",
          "width": "800",
          "height": "480",
          "time": new DateTime.now().millisecondsSinceEpoch.toString(),
        })).toString();
  }

  void updateScreen() {
    if (updateScreenPeriodically) {
      runLater(SCREEN_UPDATE_INTERVAL, () => reloadScreenshot());
    }
  }

  void clickScreen(MouseEvent e, var detail, Element target) {
    const int GAME_AREA_WIDTH = 800;
    const int GAME_AREA_HEIGHT = 480;
    var request = serverClick.resolveUri(new Uri(queryParameters: {
      "x": (GAME_AREA_WIDTH * (e.offset.x / target.client.width))
          .toStringAsFixed(0),
      "y": (GAME_AREA_HEIGHT * (e.offset.y / target.client.height))
          .toStringAsFixed(0),
    }));
    HttpRequest.getString(request.toString());
    if (!updateScreenPeriodically) {
      updateScreenPeriodically = true;
      reloadScreenshot();
    }
  }

  void toggleUpdateScreenPeriodically() {
    updateScreenPeriodically = !updateScreenPeriodically;
    reloadScreenshot();
  }

  void setAutoManipulatorSchedules(bool enabled,
                                   List<ScheduleFragment> schedules) {
    var request = serverSetAutoManipulatorSchedules.resolveUri(
        new Uri(queryParameters: {
          "enabled": enabled ? "true" : "false",
          "schedule": schedules.map(
              (fragment) => "${fragment.start}:${fragment.end}").join(";"),
    }));
    HttpRequest.getString(request.toString());
  }

  void toggleAutoManipulatorsEnabled(MouseEvent e, var detail, Element target) {
    setAutoManipulatorSchedules(!model.autoManipulatorsEnabled,
        model.autoManipulatorSchedules);
  }

  void showModalDialog(MouseEvent e, var detail, Element target) {
    var dialogName = target.dataset["dialog"];
    querySelector("#modalDialogContainer").classes.add("in");
    var dialog = querySelector("#${dialogName}") as KcaaDialog;
    dialog.show();
    dialog.classes.remove("hidden");
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
