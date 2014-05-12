part of kcaa_model;

class Screen {
  static final Map<int, String> SCREEN_MAP = <int, String>{
    0: "不明",
    101: "スタート画面",
    2: "たぶん母港",
    200: "母港",
    201: "戦績",
    202: "図鑑",
    203: "アイテムラック",
    204: "模様替え",
    205: "任務",
    206: "アイテム屋",
    207: "出撃選択",
    208: "演習選択",
    209: "遠征選択",
    210: "編成",
    211: "補給",
    212: "改装",
    213: "入渠",
    214: "工廠",
    3: "出撃",
    300: "羅針盤",
    301: "陣形選択",
    302: "戦闘中",
    303: "夜戦選択",
    304: "夜戦中",
    305: "戦闘結果",
    306: "進撃選択",
    4: "演習",
    400: "演習中",
    401: "夜戦選択",
    402: "演習夜戦中",
    403: "演習結果",
    5: "遠征",
    500: "遠征結果",
  };
}

class ScheduleFragment extends Observable {
  @observable int start;
  @observable int end;

  ScheduleFragment(this.start, this.end);
}

void handleScreen(Assistant assistant, AssistantModel model,
                  Map<String, dynamic> data) {
  model.screen = Screen.SCREEN_MAP[data["screen"]];
}

void handleRunningManipulators(Assistant assistant, AssistantModel model,
                               Map<String, dynamic> data) {
  model.runningManipulator = data["running_manipulator"];
  model.manipulatorsInQueue.clear();
  model.manipulatorsInQueue.addAll(data["manipulators_in_queue"]);
  model.autoManipulatorsActive = data["auto_manipulators_active"];
}