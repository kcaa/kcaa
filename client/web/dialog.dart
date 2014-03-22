import 'dart:html';
import 'package:polymer/polymer.dart';

import 'model/assistant.dart';

class DialogMixin {
  void close() {
    querySelector("#modalDialogContainer").classes.remove("in");
    (this as HtmlElement).classes.add("hidden");
  }
}

@CustomTag('kcaa-schedule-dialog')
class ScheduleDialog extends PolymerElement with DialogMixin {
  ScheduleDialog.created() : super.created();

  void ok() {
    close();
  }
}