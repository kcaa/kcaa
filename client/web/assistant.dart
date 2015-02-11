library kcaa_assistant;

import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'package:bootjack/bootjack.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:polymer/polymer.dart';

import 'dialog/dialog.dart';
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
  Uri serverGetObjectTypes;
  Uri serverGetObject;
  Uri serverRequestObject;
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
    "BuildDock": handleBuildDock,
    "EquipmentDefinitionList": handleEquipmentDefinitionList,
    "EquipmentList": handleEquipmentList,
    "FleetList": handleFleetList,
    "MissionList": handleMissionList,
    "PlayerInfo": handlePlayerInfo,
    "PlayerResources": handlePlayerResources,
    "PracticeList": handlePracticeList,
    "Preferences": handlePreferences,
    "QuestList": handleQuestList,
    "RepairDock": handleRepairDock,
    "RunningManipulators": handleRunningManipulators,
    "Screen": handleScreen,
    "ShipDefinitionList": handleShipDefinitionList,
    "ShipList": handleShipList,
  };
  // Referenced objects. If the object list contains these object types, the
  // client processes them first so that other object handlers can reference the
  // contents of them.
  static final List<String> REFERENCED_OBJECTS = <String>[
    "EquipmentDefinitionList",
    "EquipmentList",
    "ShipDefinitionList",
    "ShipList",
    "MissionList",
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
    model.debug = debug;

    serverRoot = clientRoot.resolve("/");
    serverGetObjects = serverRoot.resolve("get_objects");
    serverGetNewObjects = serverRoot.resolve("get_new_objects");
    serverGetObjectTypes = serverRoot.resolve("get_object_types");
    serverGetObject = serverRoot.resolve("get_object");
    serverRequestObject = serverRoot.resolve("request_object");
    serverReloadKCSAPIModules = serverRoot.resolve("reload_kcsapi");
    serverReloadManipulatorModules = serverRoot.resolve("reload_manipulators");
    serverManipulate = serverRoot.resolve("manipulate");
    serverSetPreferences = serverRoot.resolve("set_preferences");
    serverTakeScreenshot = serverRoot.resolve("take_screenshot");
    serverClick = serverRoot.resolve("click");
  }

  @override
  void attached() {
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

    model.shipList = $["shiplist"];
    model.equipmentList = $["equipmentlist"];

    addCollapseButtons();
    updateCollapsedSections();
    reloadAllObjects().then((_) => updateAvailableObjectsPeriodically());
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

  CollapsedSectionInfo toggleCollapseSectionAndShipList(MouseEvent e) {
    var info = toggleCollapseSection(e);
    // Enable the big ship list element when the section is first expanded.
    if (!info.collapsed) {
      model.shipList.disabled = false;
    }
    return info;
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
      // Skip if a collapse button is added manually.
      if (header.querySelector("button.collapse") != null) {
        continue;
      }
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

  void filterShips(Event e, var detail, Element target) {
    var filterType = target.dataset["filterType"];
    var filter = Ship.SHIP_FILTER[filterType];
    model.numFilteredShips = model.ships.where((ship) => filter(ship)).length;
    model.shipList.filter = filter;
  }

  void filterShipsByTag(Event e, var detail, Element target) {
    var tag = target.dataset["tag"];
    var filter = Ship.makeFilterByTag(tag);
    model.numFilteredShips = model.ships.where((ship) => filter(ship)).length;
    model.shipList.filter = filter;
    e.preventDefault();
  }

  Future reloadAllObjects() {
    return handleObjects(serverGetObjects);
  }

  void handleObject(String objectType, String data) {
    var handler = OBJECT_HANDLERS[objectType];
    if (handler != null) {
      handler(this, model, JSON.decode(data));
    }
  }

  Future handleObjects(Uri objectsUri) {
    return HttpRequest.getString(objectsUri.toString())
      .then((String content) {
        var objects = JSON.decode(content) as Map<String, String>;
        var objectTypes = new List<String>();
        // Handle referenced objects first.
        for (var referencedObject in REFERENCED_OBJECTS) {
          if (objects.containsKey(referencedObject)) {
            objectTypes.add(referencedObject);
          }
        }
        // Then handle the rest.
        var internalHandlerChain = new Future.value(null);
        for (var objectType in objects.keys) {
          if (!REFERENCED_OBJECTS.contains(objectType)) {
            objectTypes.add(objectType);
          }
        }
        var handlerChain = new Future.value();
        for (var objectType in objectTypes) {
          handlerChain = handlerChain.then((_) {
            handleObject(objectType, objects[objectType]);
            // Delay the next handling and let the renderer renders the handled
            // data.
            return new Future.delayed(const Duration(milliseconds: 0));
          });
        }
        return handlerChain;
      });
  }

  Future updateAvailableObjects() {
    // Update the list of available objects in the debug info section.
    return HttpRequest.getString(serverGetObjectTypes.toString())
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
      }).then((_) {
        // Actually handles the new objects.
        return handleObjects(serverGetNewObjects);
      });
  }

  void updateAvailableObjectsPeriodically() {
    updateAvailableObjects().then((_) {
      runLater(updateAvailableObjectsIntervalMs,
          updateAvailableObjectsPeriodically);
    },
    onError: (_) {
      runLater(updateAvailableObjectsIntervalMs,
          updateAvailableObjectsPeriodically);
    });
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

  Future<Map<String, dynamic>> requestObject(
      String type, Map<String, String> parameters) {
    parameters.addAll(<String, String> {
      "type": type,
    });
    var request = serverRequestObject.resolveUri(
        new Uri(queryParameters: parameters));
    return HttpRequest.getString(request.toString())
        .then((String content) {
          var json = JSON.decode(content);
          return json;
        });
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
      runLater(2000, () => reloadScreenshot());
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

  void showModalDialogByName(String dialogName, Element target) {
    querySelector("#modalDialogContainer").classes.add("in");
    var dialog = querySelector("#${dialogName}") as KcaaDialog;
    dialog.show(target);
    dialog.classes.remove("hidden");
  }

  void showModalDialog(MouseEvent e, var detail, Element target) {
    var dialogName = target.dataset["dialog"];
    showModalDialogByName(dialogName, target);
    e.preventDefault();
  }

  void savePreferences() {
    HttpRequest.postFormData(serverSetPreferences.toString(), {
      "prefs": model.preferences.toJSON(),
    });
  }

  void saveFleet(MouseEvent e, var detail, Element target) {
    var fleetId = target.dataset["fleetId"];
    // TODO: Consider passing dataset map rather than Element to
    // KcaaDialog.show().
    Element dummy = new DivElement();
    dummy.dataset["dialog"] = "kcaaFleetOrganizationDialog";
    dummy.dataset["fleetId"] = fleetId;
    showModalDialog(new MouseEvent(""), null, dummy);
  }

  void loadFleet(MouseEvent e, var detail, Element target) {
    var fleetName = target.dataset["name"];
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "LoadFleet",
          "fleet_id": "1",  // Always load to the 1st fleet
          "saved_fleet_name": fleetName,
        }));
    HttpRequest.getString(request.toString());
  }

  void checkPracticeOpponents() {
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "CheckPracticeOpponents",
        }));
    HttpRequest.getString(request.toString());
  }

  void handlePractice(MouseEvent e, var detail, Element target) {
    var practiceId = target.dataset["practiceId"];
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "HandlePractice",
          "fleet_id": "1",  // Always use the 1st fleet
          "practice_id": practiceId,
        }));
    HttpRequest.getString(request.toString());
  }

  void handleAllPractices(MouseEvent e, var detail, Element target) {
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "HandleAllPractices",
          "fleet_id": "1",  // Always use the 1st fleet
        }));
    HttpRequest.getString(request.toString());
  }

  void warmUpFleet(MouseEvent e, var detail, Element target) {
    var fleetId = target.dataset["fleetId"];
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "WarmUpFleet",
          "fleet_id": fleetId,
        }));
    HttpRequest.getString(request.toString());
  }

  void enhanceBestShip(MouseEvent e, var detail, Element target) {
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "EnhanceBestShip",
        }));
    HttpRequest.getString(request.toString());
  }

  void warmUpIdleShips(MouseEvent e, var detail, Element target) {
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "WarmUpIdleShips",
          "fleet_id": "1",
          "num_ships": "6",
        }));
    HttpRequest.getString(request.toString());
  }

  void goOnExpedition(MouseEvent e, var detail, Element target) {
    var fleetId = target.dataset["fleetId"];
    var mapareaId =
        (target.parent.querySelector(".mapareaId") as InputElement).value;
    var mapId = (target.parent.querySelector(".mapId") as InputElement).value;
    var formation = model.formations.value;
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "GoOnExpedition",
          "fleet_id": fleetId,
          "maparea_id": mapareaId,
          "map_id": mapId,
          "formation": formation,
        }));
    HttpRequest.getString(request.toString());
  }

  void boostShipRepairing(Event e, var detail, Element target) {
    var slotId = int.parse(target.dataset["slotId"]);
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "BoostShipRepairing",
          "slot_id": slotId.toString(),
        }));
    HttpRequest.getString(request.toString());
  }

  void buildShip() {
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "BuildShip",
          "fuel": model.buildFuel,
          "ammo": model.buildAmmo,
          "steel": model.buildSteel,
          "bauxite": model.buildBauxite,
          "grand": model.grandBuilding.toString(),
          "material": model.buildMaterial.value,
        }));
    HttpRequest.getString(request.toString());
  }

  void boostShipBuilding(Event e, var detail, Element target) {
    var slotId = int.parse(target.dataset["slotId"]);
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "BoostShipBuilding",
          "slot_id": slotId.toString(),
        }));
    HttpRequest.getString(request.toString());
  }

  void receiveShip(Event e, var detail, Element target) {
    var slotId = int.parse(target.dataset["slotId"]);
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "ReceiveShip",
          "slot_id": slotId.toString(),
        }));
    HttpRequest.getString(request.toString());
  }

  void developEquipment() {
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "DevelopEquipment",
          "fuel": model.developFuel,
          "ammo": model.developAmmo,
          "steel": model.developSteel,
          "bauxite": model.developBauxite,
        }));
    HttpRequest.getString(request.toString());
  }

  void deleteShipTag(Event e, var detail, Element target) {
    var tag = target.dataset["tag"];
    var shipPrefs = model.preferences.shipPrefs;
    for (var ship in model.ships) {
      if (!ship.tags.contains(tag)) {
        continue;
      }
      ship.tags.remove(tag);
      var prefsTags = shipPrefs.tags[ship.id];
      prefsTags.tags.remove(tag);
      if (prefsTags.tags.isEmpty) {
        shipPrefs.tags.remove(ship.id);
      }
    }
    savePreferences();
    updateShipTags(model);
  }

  void chargeAllFleets() {
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "ChargeAllFleets",
        }));
    HttpRequest.getString(request.toString());
  }

  void dissolveLeastValuableShips() {
    Uri request = serverManipulate.resolveUri(
        new Uri(queryParameters: {
          "type": "DissolveLeastValuableShips",
        }));
    HttpRequest.getString(request.toString());
  }
}