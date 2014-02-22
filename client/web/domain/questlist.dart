part of kcaa;

class Quest {
  static final Map<int, String> CATEGORY_MAP = <int, String>{
    1: "編成",
    2: "出撃",
    3: "演習",
    4: "遠征",
    5: "補給",
    6: "工廠",
    7: "改装",
  };
  static final Map<int, String> STATE_MAP = <int, String>{
    1: "",
    2: "active",
    3: "complete",
  };
  static final Map<int, String> CYCLE_MAP = <int, String>{
    1: "一回",
    2: "日毎",
    3: "週毎",
  };

  int id;
  String name;
  String description;
  String category;
  String state;
  int fuel, ammo, steel, bauxite;
  int progress;
  String cycle;

  Quest(Map<String, dynamic> data)
      : id = data["id"],
        name = data["name"],
        description = data["description"],
        category = CATEGORY_MAP[data["category"]],
        state = STATE_MAP[data["state"]],
        fuel = data["rewards"]["fuel"],
        ammo = data["rewards"]["ammo"],
        steel = data["rewards"]["steel"],
        bauxite = data["rewards"]["bauxite"],
        progress = data["progress"],
        cycle = CYCLE_MAP[data["cycle"]] {}
}

void handleQuestList(Assistant assistant, Map<String, dynamic> data) {
  assistant.numQuests = data["count"];
  assistant.numQuestsUndertaken = data["count_undertaken"];
  assistant.quests.clear();
  for (var questData in data["quests"]) {
    assistant.quests.add(new Quest(questData));
  }
}