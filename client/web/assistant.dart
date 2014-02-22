library kcaa;

import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'package:polymer/polymer.dart';

part 'questlist.dart';
part 'util.dart';

@CustomTag('eplusx-kancolle-assistant')
class Assistant extends PolymerElement {
  // Quests.
  @observable int numQuests = 0;
  @observable int numQuestsUndertaken = 0;
  final List<Quest> quests = new ObservableList<Quest>();

  // Server URIs.
  Uri clientRoot;
  Uri serverRoot;
  Uri serverGetNewObjects;
  Uri serverGetObject;
  Uri serverReloadKCSAPIModules;

  // Debug information.
  @observable String debugInfo;
  final List<String> availableObjects = new ObservableList<String>();
  Set<String> availableObjectSet = new Set<String>();
  Timer availableObjectsChecker;

  // Object handlers.
  final Map<String, Function> OBJECT_HANDLERS = <String, Function>{
    "QuestList": handleQuestList,
  };

  Assistant.created() : super.created();

  @override
  void enteredView() {
    clientRoot = Uri.parse(window.location.href);
    serverRoot = clientRoot.resolve("/");
    serverGetNewObjects = serverRoot.resolve("get_new_objects");
    serverGetObject = serverRoot.resolve("get_object");
    serverReloadKCSAPIModules = serverRoot.resolve("reload_kcsapi");
    availableObjectsChecker =
        new Timer.periodic(MILLISECOND * 100, (Timer timer) {
      updateAvailableObjects();
    });

    addCollapseButtons();
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

  void updateAvailableObjects() {
    HttpRequest.getString(serverGetNewObjects.toString())
        .then((String content) {
          List<String> newObjects = JSON.decode(content);
          var newObjectFound = false;
          for (var objectType in newObjects) {
            newObjectFound =
                availableObjectSet.add(objectType) || newObjectFound;
            var handler = OBJECT_HANDLERS[objectType];
            if (handler != null) {
              handler(this);
            }
          }
          if (newObjectFound) {
            var sortedObjects = availableObjectSet.toList(growable: false);
            sortedObjects.sort();
            availableObjects.clear();
            availableObjects.addAll(sortedObjects);
          }
        });
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