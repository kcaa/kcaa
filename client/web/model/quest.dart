part of kcaa_model;

class Quest extends Observable {
  static final Map<int, String> CATEGORY_MAP = <int, String>{
    1: "編成",
    2: "出撃",
    3: "演習",
    4: "遠征",
    5: "補給",
    6: "工廠",
    7: "改装",
  };
  static final Map<int, String> STATE_CLASS_MAP = <int, String>{
    1: "",
    2: "active",
    3: "complete",
  };
  static final Map<int, String> CYCLE_MAP = <int, String>{
    1: "一回",
    2: "日毎",
    3: "週毎",
  };

  @observable int id;
  @observable String name;
  @observable String description;
  @observable String category;
  @observable int state;
  @observable String stateClass;
  @observable int fuel, ammo, steel, bauxite;
  @observable int progress;
  @observable String cycle;

  Quest();

  void update(Map<String, dynamic> data) {
    id = data["id"];
    name = data["name"];
    description = data["description"];
    category = CATEGORY_MAP[data["category"]];
    state = data["state"];
    stateClass = STATE_CLASS_MAP[data["state"]];
    fuel = data["rewards"]["fuel"];
    ammo = data["rewards"]["ammo"];
    steel = data["rewards"]["steel"];
    bauxite = data["rewards"]["bauxite"];
    progress = data["progress"];
    cycle = CYCLE_MAP[data["cycle"]];
  }
}
