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

@CustomTag('eplusx-kancolle-assistant')
class Assistant extends PolymerElement {
  @observable String debugInfo;
  final List<String> newObjects = new ObservableList<String>();
  final List<String> activeQuests = new ObservableList<String>();

  Uri clientRoot;
  Uri serverRoot;
  Uri serverGetNewObjects;
  Uri serverGetObject;

  Timer newObjectsChecker;

  Assistant.created() : super.created();

  @override
  void enteredView() {
    clientRoot = Uri.parse(window.location.href);
    serverRoot = clientRoot.resolve("/");
    serverGetNewObjects = serverRoot.resolve("/get_new_objects");
    serverGetObject = serverRoot.resolve("/get_object");
    newObjectsChecker = new Timer.periodic(MILLISECOND * 100, (Timer timer) {
      getNewObjects();
    });
  }

  void getNewObjects() {
    HttpRequest.getString(serverGetNewObjects.toString())
        .then((String content) {
          List<String> objectTypes = JSON.decode(content);
          if (!iterableEquals(newObjects, objectTypes)) {
            newObjects.clear();
            newObjects.addAll(objectTypes);
          }
        });
  }

  void getObject(String type) {
    Uri request = serverGetObject.resolveUri(new Uri(queryParameters: {
      "type": type,
    }));
    HttpRequest.getString(request.toString())
        .then((String content) {
          var json = JSON.decode(content);
          debugInfo = formatJson(json);
        });
  }

  void getObjectFromName(Event e, var detail, Element target) {
    getObject(target.text);
  }

  void collapseSection(Event e, var detail, Element target) {
    var toCollapse = target.dataset["collapsed"] != "true";
    print(toCollapse);
    for (var element in target.parent.parent.children) {
      if (element == target.parent) {
        continue;
      }
      element.classes.toggle("hidden", toCollapse);
    }
    target.text = toCollapse ? "▼" : "►";
    target.dataset["collapsed"] = (toCollapse).toString();
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