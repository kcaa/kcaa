import 'dart:html';
import 'package:polymer/polymer.dart';

import 'model/assistant.dart';

class DialogMixin {
  void closeDialog() {
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

  void close() {
    // Seems like dart2js can't recognize a method from a mixin...
    closeDialog();
  }
}