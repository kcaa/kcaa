import 'dart:html';
import 'package:bootjack/bootjack.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:polymer/polymer.dart';

import 'assistant.dart';
import 'model/assistant.dart';

main() {
  // Theoretically this is not safe, as some data requiring ja_JP date format
  // may run before loading completes, but that would never happen in reality.
  initializeDateFormatting("ja_JP", null).then((_) => null);
  Modal.use();
  initPolymer();
  (querySelector("#kcaaAssistant") as Assistant).model = new AssistantModel();
}