library kcaa_dialog;

import 'dart:html';
import 'package:polymer/polymer.dart';

import 'model/assistant.dart';

class KcaaDialog extends PolymerElement {
  KcaaDialog.created() : super.created();

  @observable
  void close() {
    querySelector("#modalDialogContainer").classes.remove("in");
    this.classes.add("hidden");
  }
}

@CustomTag('kcaa-schedule-dialog')
class ScheduleDialog extends KcaaDialog {
  ScheduleDialog.created() : super.created();

  void ok() {
    close();
  }
}