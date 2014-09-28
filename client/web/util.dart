library kcaa_util;

import 'dart:async';
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

class ReverseMapBuilder<K, V> {
  Map<K, V> buildFrom(Map<V, K> map) {
    var reverseMap = new Map<K, V>();
    for (var key in map.keys) {
      reverseMap[map[key]] = key;
    }
    return reverseMap;
  }
}

class Candidate<E> extends Observable {
  @observable E id;
  @observable String name;

  Candidate(this.id, this.name);
}

typedef void Updator<E>(E value, Element target);

class KSelection<E> extends Observable {
  @observable E value;
  @observable final List<Candidate> candidates;

  KSelection(this.candidates);
}

class KSelectionBuilder<E> {
  KSelection<E> buildFrom(List list) {
    var candidates = new ObservableList<Candidate<E>>();
    for (List entry in list) {
      if (entry.length != 2) {
        throw new Exception(
            "Candidate entry must has 2 elements, but got ${entry}");
      }
      candidates.add(new Candidate<E>(entry[0], entry[1]));
    }
    return new KSelection(candidates);
  }
}

void appendIndentedText(String text, int level, StringBuffer buffer) {
  var indentationMark = "  ";
  for (var i = 0; i < level; ++i) {
    buffer.write(indentationMark);
  }
  buffer.write(text);
}

String formatJson(json) {
  void formatJsonInternal(json, int level, bool firstLineIndented,
                          StringBuffer buffer) {
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
        formatJsonInternal(json[key], level + 1, true, buffer);
      }
      appendIndentedText("},\n", level, buffer);
    } else if (json is List) {
      buffer.write("[\n");
      for (var value in json) {
        formatJsonInternal(value, level + 1, false, buffer);
      }
      appendIndentedText("],\n", level, buffer);
    } else if (json is String) {
      buffer.write('"${json.toString()}",\n');
    }
    else {
      buffer.write("${json.toString()},\n");
    }
  }
  var buffer = new StringBuffer();
  formatJsonInternal(json, 0, false, buffer);
  return buffer.toString();
}