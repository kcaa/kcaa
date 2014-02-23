part of kcaa;

class Screen {
  static final Map<int, String> SCREEN_MAP = <int, String>{
    0: "不明",
    1: "スタート画面",
    200: "母港",
    201: "戦績",
    202: "図鑑",
    203: "アイテムラック",
    204: "模様替え",
    205: "任務",
    206: "アイテム屋",
  };
}

void handleScreen(Assistant assistant, Map<String, dynamic> data) {
  assistant.screen = Screen.SCREEN_MAP[data["screen"]];
}