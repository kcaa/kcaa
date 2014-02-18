library kaa;

import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'package:polymer/polymer.dart';

const MILLISECOND = const Duration(milliseconds: 1);

Timer runLater(int milliseconds, void callback()) {
  return new Timer(MILLISECOND * milliseconds, callback);
}

bool iterableEquals(Iterable a, Iterable b) {
  var ai = a.iterator;
  var bi = b.iterator;
  var different = false;
  while (true) {
    var aHasNext = ai.moveNext();
    var bHasNext = bi.moveNext();
    if (!aHasNext || !bHasNext) {
      return aHasNext == bHasNext;
    }
    if (ai.current != bi.current) {
      return false;
    }
  }
}

class Quest {
  int id;
  String name;
  String description;

  Quest(this.id, this.name, this.description) {}
}

@CustomTag('eplusx-kancolle-assistant')
class Assistant extends PolymerElement {
  @observable String debugInfo;
  final List<String> availableObjects = new ObservableList<String>();
  Set<String> availableObjectSet = new Set<String>();

  final List<String> activeQuests = new ObservableList<String>();

  @observable int numQuests = 0;
  @observable int numQuestsUndertaken = 0;
  final List<Quest> quests = new ObservableList<Quest>();

  Uri clientRoot;
  Uri serverRoot;
  Uri serverGetNewObjects;
  Uri serverGetObject;

  Timer availableObjectsChecker;

  Assistant.created() : super.created();

  @override
  void enteredView() {
    clientRoot = Uri.parse(window.location.href);
    serverRoot = clientRoot.resolve("/");
    serverGetNewObjects = serverRoot.resolve("/get_new_objects");
    serverGetObject = serverRoot.resolve("/get_object");
    availableObjectsChecker = new Timer.periodic(MILLISECOND * 100, (Timer timer) {
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
                newObjectFound || availableObjectSet.add(objectType);

            // TODO: Use function lookup table (objectType -> function).
            if (objectType == "QuestList") {
              handleQuestList();
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

  void handleQuestList() {
    getObject("QuestList", false).then((Map<String, dynamic> data) {
      numQuests = data["count"];
      numQuestsUndertaken = data["count_undertaken"];
      quests.clear();
      for (var quest in data["quests"]) {
        quests.add(new Quest(quest["id"], quest["name"],
            quest["description"]));
      }
    });
  }

  static void appendIndentedText(String text, int level, StringBuffer buffer) {
    var indentationMark = "  ";
    for (var i = 0; i < level; ++i) {
      buffer.write(indentationMark);
    }
    buffer.write(text);
  }

  static String formatJson(json, [int level=0, bool firstLineIndented=false]) {
    var buffer = new StringBuffer();
    if (!firstLineIndented) {
      appendIndentedText("", level, buffer);
    }
    if (json is Map) {
      buffer.write("{\n");
      var keys = new List.from(json.keys, growable: false);
      keys.sort();
      for (var key in keys) {
        appendIndentedText('"${key}"', level + 1, buffer);
        buffer.write(": ");
        buffer.write(formatJson(json[key], level + 1, true));
      }
      appendIndentedText("}\n", level, buffer);
    } else if (json is List) {
      buffer.write("[\n");
      for (var value in json) {
        buffer.write(formatJson(value, level + 1, false));
      }
      appendIndentedText("]\n", level, buffer);
    } else if (json is String) {
      buffer.write('"${json.toString()}"\n');
    }
    else {
      buffer.write("${json.toString()}\n");
    }
    return buffer.toString();
  }
}