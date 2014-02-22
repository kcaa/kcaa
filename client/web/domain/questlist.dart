part of kcaa;

class Quest {
  int id;
  String name;
  String description;
  String category;
  String state;
  int fuel, ammo, steel, bauxite;
  int progress;
  String cycle;

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

  Quest(this.id, this.name, this.description, int category, int state,
      Map<String, int> rewards, int progress, int cycle)
      : category = CATEGORY_MAP[category],
        state = STATE_MAP[state],
        fuel = rewards["fuel"],
        ammo = rewards["ammo"],
        steel = rewards["steel"],
        bauxite = rewards["bauxite"],
        progress = progress,
        cycle = CYCLE_MAP[cycle] {}
}

void handleQuestList(Assistant assistant) {
  assistant.getObject("QuestList", false).then((Map<String, dynamic> data) {
    assistant.numQuests = data["count"];
    assistant.numQuestsUndertaken = data["count_undertaken"];
    assistant.quests.clear();
    for (var quest in data["quests"]) {
      assistant.quests.add(new Quest(quest["id"], quest["name"],
          quest["description"], quest["category"], quest["state"],
          quest["rewards"], quest["progress"], quest["cycle"]));
    }
  });
}