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
  Uri serverSetPreferences;
  Uri serverTakeScreenshot;
  Uri serverClick;

  // Debug information.
  bool debug = false;
  @observable String debugInfo;
  final List<String> availableObjects = new ObservableList<String>();
  Set<String> availableObjectSet = new Set<String>();
  Timer availableObjectsChecker;
  int updateAvailableObjectsIntervalMs;
  bool showScreen = true;
  @observable bool updateScreenPeriodically = false;

  // Object handlers.
  static final Map<String, Function> OBJECT_HANDLERS = <String, Function>{
    "FleetList": handleFleetList,
    "MissionList": handleMissionList,
    "Preferences": handlePreferences,
    "QuestList": handleQuestList,
    "RepairDock": handleRepairDock,
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

    clientRoot = Uri.parse(window.location.href);
    var interval = clientRoot.queryParameters["interval"];
    interval = interval != null ? double.parse(interval) : 1.0;
    updateAvailableObjectsIntervalMs = (1000 * interval).toInt();
    debug = clientRoot.queryParameters["debug"] == "true";
    showScreen = clientRoot.queryParameters["screen"] != "false";

    serverRoot = clientRoot.resolve("/");
    serverGetObjects = serverRoot.resolve("get_objects");
    serverGetNewObjects = serverRoot.resolve("get_new_objects");
    serverGetObject = serverRoot.resolve("get_object");
    serverReloadKCSAPIModules = serverRoot.resolve("reload_kcsapi");
    serverReloadManipulatorModules = serverRoot.resolve("reload_manipulators");
    serverManipulate = serverRoot.resolve("manipulate");
    serverSetPreferences = serverRoot.resolve("set_preferences");
    serverTakeScreenshot = serverRoot.resolve("take_screenshot");
    serverClick = serverRoot.resolve("click");
  }

  @override
  void enteredView() {
    if (debug) {
      $["debugControlsSection"].classes.remove("hidden");
      $["debugInfoSection"].classes.remove("hidden");
    }
    if (showScreen) {
      $["screenSection"].classes.remove("hidden");
      runLater(1000, () => reloadScreenshot());
    }

    // Somehow on-transition-end event handler doesn't work.
    $["clickMarker"].onTransitionEnd.listen(endClickVisibleFeedback);

    runLater(updateAvailableObjectsIntervalMs,
        updateAvailableObjectsPeriodically);
    addCollapseButtons();
    updateCollapsedSections();
    addShipSortLabels();
    handleObjects(serverGetObjects);
    // TODO: Ensure this happens after all other dialog elements are
    // initialized.
    runLater(1000, () => passModelToDialogs());
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

  void addShipSortLabels() {
    for (Element columnHeader in
        shadowRoot.querySelectorAll("table.shipList th[data-type]")) {
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
    model.shipComparer = Ship.SHIP_COMPARER[type];
    // Determine the sort order.
    if (order != "descending") {
      model.shipOrderInverter = Ship.orderInDescending;
      sortLabel.text = label + "▼";
      columnHeader.dataset["order"] = "descending";
    } else {
      model.shipOrderInverter = Ship.orderInAscending;
      sortLabel.text = label + "▲";
      columnHeader.dataset["order"] = "ascending";
    }
    // Sort the ships using these criteria.
    reorderShipList(model);
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
    var screenshot = $["screenshot"] as ImageElement;
    screenshot.classes.add("loading");
    screenshot.src = serverTakeScreenshot.resolveUri(
        new Uri(queryParameters: {
          "format": "jpeg",
          "quality": "50",
          "width": "800",
          "height": "480",
          "time": new DateTime.now().millisecondsSinceEpoch.toString(),
        })).toString();
  }

  void updateScreen() {
    $["screenshot"].classes.remove("loading");
    if (updateScreenPeriodically) {
      runLater(SCREEN_UPDATE_INTERVAL, () => reloadScreenshot());
    }
  }

  void showClickVisibleFeedback(MouseEvent e) {
    var clickMarker = $["clickMarker"];
    clickMarker.dataset["state"] = "expanding";
    clickMarker.style.opacity = "1";
    clickMarker.style.left = "${e.offset.x - clickMarker.client.width / 2}px";
    clickMarker.style.top = "${e.offset.y - clickMarker.client.height / 2}px";
    clickMarker.style.transform = "scale(1, 1)";
    clickMarker.style.transitionDuration = "300ms";
    clickMarker.style.transitionTimingFunction = "ease-out";
  }

  void endClickVisibleFeedback(TransitionEvent e) {
    var clickMarker = e.target as Element;
    switch (clickMarker.dataset["state"]) {
      case "expanding":
        clickMarker.dataset["state"] = "blurring";
        clickMarker.style.opacity = "0";
        clickMarker.style.transform = "scale(1.2, 1.2)";
        clickMarker.style.transitionDuration = "500ms";
        clickMarker.style.transitionTimingFunction = "ease-in";
        return;
      case "blurring":
        clickMarker.dataset["state"] = "exiting";
        clickMarker.style.transform = "scale(0, 0)";
        clickMarker.style.transitionDuration = "0ms";
        clickMarker.style.transitionTimingFunction = "linear";
        return;
    }
  }

  void clickScreen(MouseEvent e, var detail, Element target) {
    showClickVisibleFeedback(e);

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
      runLater(1000, () => reloadScreenshot());
    }
  }

  void toggleUpdateScreenPeriodically() {
    updateScreenPeriodically = !updateScreenPeriodically;
    reloadScreenshot();
  }

  void setAutoManipulatorSchedules(bool enabled,
                                   List<ScheduleFragment> schedules) {
    model.preferences.automanPrefs.enabled = enabled;
    model.preferences.automanPrefs.schedules.clear();
    model.preferences.automanPrefs.schedules.addAll(schedules);
    savePreferences();
  }

  void showModalDialog(MouseEvent e, var detail, Element target) {
    var dialogName = target.dataset["dialog"];
    querySelector("#modalDialogContainer").classes.add("in");
    var dialog = querySelector("#${dialogName}") as KcaaDialog;
    dialog.show(target);
    dialog.classes.remove("hidden");
  }

  void savePreferences() {
    HttpRequest.postFormData(serverSetPreferences.toString(), {
      "prefs": model.preferences.toJSON(),
    });
  }

  void saveFleet(MouseEvent e, var detail, Element target) {
    var fleetId = int.parse(target.dataset["fleetId"]);
    var fleet = model.fleets[fleetId - 1];
    model.preferences.fleetPrefs.saveFleet(fleet.name, fleet.ships);
    savePreferences();
  }
}
