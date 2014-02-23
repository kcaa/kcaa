part of kcaa;

class Screen {
  static final Map<int, String> SCREEN_MAP = <int, String>{
    0: "スタート画面",
    1: "母港",
  };
}

void handleScreen(Assistant assistant, Map<String, dynamic> data) {
  assistant.screen = Screen.SCREEN_MAP[data["screen"]];
}