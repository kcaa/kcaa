library kaa;

import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'package:polymer/polymer.dart';

@CustomTag('eplusx-kancolle-assistant')
class Assistant extends PolymerElement {
  @observable String peekResult;

  Assistant.created() : super.created();

  @override
  void enteredView() {
  }

  void peek() {
    var path = "http://localhost:9090/proxy/9091/har";
    HttpRequest.getString(path)
        .then((String content) {
          var json = JSON.decode(content);
          peekResult = formatJson(json);
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