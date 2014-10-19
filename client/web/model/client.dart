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
    21200: "近代化改修結果",
    21201: "改造結果",
    213: "入渠",
    214: "工廠",
    21400: "建造完了",
    21401: "開発完了",
    3: "出撃",
    300: "羅針盤",
    301: "航海中",
    302: "陣形選択",
    303: "戦闘中",
    304: "夜戦選択",
    305: "夜戦中",
    306: "戦闘結果",
    307: "戦闘報酬",
    308: "進撃選択",
    309: "出撃結果",
    4: "演習",
    400: "演習中",
    401: "夜戦選択",
    402: "演習夜戦中",
    403: "演習結果",
    5: "遠征",
    500: "遠征結果",
  };
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

  // Change the document title if there is a running manipulator.
  var title = querySelector("title") as TitleElement;
  if (model.runningManipulator != null) {
    title.text = "${model.runningManipulator} - ${title.title}";
  } else {
    title.text = title.title;
  }
}
