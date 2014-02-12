library kaa;

import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'package:polymer/polymer.dart';

@CustomTag('eplusx-kancolle-assistant')
class Assistant extends PolymerElement {
  @observable String debugInfo;
  final List<String> activeQuests = new ObservableList<String>();

  Uri serverGetNewObjects;
  Uri serverGetObject;

  Assistant.created() : super.created();

  @override
  void enteredView() {
    var clientRoot = Uri.parse(window.location.href);
    serverGetNewObjects = clientRoot.resolve("/get_new_objects");
    serverGetObject = clientRoot.resolve("/get_object");
  }

  void getNewObjects() {
    HttpRequest.getString(serverGetNewObjects.toString())
        .then((String content) {
          var json = JSON.decode(content);
          debugInfo = formatJson(json);
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

  void getQuestList() {
    getObject("QuestList");
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