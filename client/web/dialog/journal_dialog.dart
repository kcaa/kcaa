import 'dart:async';
import 'dart:html';
import 'dart:js';
import 'package:polymer/polymer.dart';

import 'dialog.dart';

class LineChart {
  JsObject dataTable;
  JsObject dataView;
  JsObject chart;
  Map<String, dynamic> options;
  Map<String, dynamic> rangeOptions;

  LineChart(Element element, Map<String, dynamic> data,
      Map<String, dynamic> options) {
    var visualization = context["google"]["visualization"] as JsObject;
    dataTable = new JsObject(visualization["DataTable"],
        [new JsObject.jsify(data)]);
    dataView = new JsObject(visualization["DataView"], [dataTable]);
    chart = new JsObject(visualization["LineChart"], [element]);
    this.options = options;
    rangeOptions = {};
    draw();
  }

  void draw() {
    var options = new Map<String, dynamic>.from(this.options);
    options.addAll(rangeOptions);
    chart.callMethod("draw", [dataView, new JsObject.jsify(options)]);
  }

  void setRange(Duration duration) {
    var now = new DateTime.now();
    rangeOptions = {
      "hAxis": {
        "viewWindow": {
          "max": now,
          "min": now.subtract(duration),
        }
      }
    };
    draw();
  }

  void filterSeries(List<int> seriesIndices) {
    dataView.callMethod("setColumns",
        [new JsObject.jsify(seriesIndices)]);
    draw();
  }

  static Future load() {
    Completer c = new Completer();
    context["google"].callMethod("load",
        ["visualization",
         "1",
         new JsObject.jsify({
          "packages": ["corechart"],
          "callback": new JsFunction.withThis(c.complete)
        })]);
    return c.future;
  }
}

@CustomTag('kcaa-journal-dialog')
class JournalDialog extends KcaaDialog {
  LineChart chart;
  @observable final List<String> labels = new ObservableList<String>();

  JournalDialog.created() : super.created();

  @override
  void show(Element target) {
    var type = target.dataset["type"];
    var subtype = target.dataset["subtype"];
    ($["chart"] as Element).children.clear();
    labels.clear();
    var loadFuture = LineChart.load();
    assistant.requestObject(type, {"subtype": subtype}).then(
        (Map<String, dynamic> data) {
      labels.addAll((data["cols"] as List).map((column) => column["label"]));
      labels.removeAt(0);

      loadFuture.then((_) {
        var now = new DateTime.now();
        chart = new LineChart($["chart"], data, {
          "animation": {
            "duration": 1000,
            "easing": "inAndOut",
          },
          "backgroundColor": "transparent",
          "explorer": {
            "axis": "horizontal",
          },
          "hAxis": {
            "viewWindow": {
              "max": now,
              "min": now.subtract(new Duration(days: 30)),
            }
          },
          "theme": "maximized",
        });
      });
    });
  }

  void setRange(MouseEvent e, var detail, Element target) {
    var duration = int.parse(target.dataset["duration"]);
    chart.setRange(new Duration(seconds: duration));
  }

  void filterSeries(MouseEvent e, var detail, Element target) {
    var index = int.parse(target.dataset["index"]);
    chart.filterSeries([0, index + 1]);
  }

  void filterSeriesAll() {
    chart.filterSeries(new List<int>.generate(labels.length + 1, (int i) => i));
  }
}