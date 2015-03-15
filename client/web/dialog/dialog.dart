library kcaa_dialog;

import 'dart:html';
import 'package:polymer/polymer.dart';
import 'package:paper_elements/paper_dialog_base.dart';

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

class KcaaPaperDialog extends PolymerElement {
  @observable AssistantModel model;
  Assistant assistant;
  PaperDialogBase dialog;

  KcaaPaperDialog.created() : super.created();

  void setup(AssistantModel model, Assistant assistant) {
    this.model = model;
    this.assistant = assistant;
    dialog = shadowRoot.querySelector("paper-dialog, paper-action-dialog");
  }

  // Called when the dialog is being shown.
  void initialize() {}

  void open() {
    dialog.open();
  }

  @observable
  void close() {
    dialog.close();
  }
}