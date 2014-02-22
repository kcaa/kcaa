part of kcaa;

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

void appendIndentedText(String text, int level, StringBuffer buffer) {
  var indentationMark = "  ";
  for (var i = 0; i < level; ++i) {
    buffer.write(indentationMark);
  }
  buffer.write(text);
}

String formatJson(json, [int level=0, bool firstLineIndented=false]) {
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