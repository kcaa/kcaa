import 'package:polymer/polymer.dart';

@CustomTag('kcaa-gauge')
class GaugeElement extends PolymerElement {
  @published num current;
  @published num extra;
  @published num min = 0;
  @published num max = 100;
  @published int precision = 2;

  GaugeElement.created() : super.created();

  int toRatio(num current) {
    if (max == min) {
      return 100;
    }
    return (100.0 * (current - min)) ~/ (max - min);
  }

  String toFixed(num current) {
    if (current == null) {
      return "";
    }
    if (current is int) {
      return current.toString();
    }
    return current.toStringAsFixed(precision);
  }
}