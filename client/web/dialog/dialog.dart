library kcaa_dialog;

import 'dart:html';
import 'package:polymer/polymer.dart';

import '../assistant.dart';
import '../model/assistant.dart';

class KcaaDialog extends PolymerElement {
  // Model and the assistant element. These values are set during the
  // initialization phase of the assistant element.
  @observable AssistantModel model;
  Assistant assistant;

  KcaaDialog.created() : super.created();

  // Called when the dialog is being shown.
  void show(Element target) {}

  @observable
  void close() {
    querySelector("#modalDialogContainer").classes.remove("in");
    this.classes.add("hidden");
  }
}