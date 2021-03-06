part of kcaa_model;

class Fleet extends Observable {
  static const int WARMUP_VITALITY = 75;

  @observable int id;
  @observable String name;
  // Somehow this list needs to be @observable for getting ships.length.
  @observable final List<Ship> ships = new ObservableList<Ship>();
  @observable String undertakingMission;
  @observable String missionEtaDatetimeString;
  @observable bool canWarmUp;
  @observable bool collapsed = null;

  Fleet();

  void update(Map<String, dynamic> data, Map<int, Ship> shipMap,
      List<Mission> missions) {
    id = data["id"];
    name = data["name"];

    var shipsLength = data["ship_ids"].length;
    if (ships.length != shipsLength) {
      if (shipsLength < ships.length) {
        ships.removeRange(shipsLength, ships.length);
      } else {
        for (var i = ships.length; i < shipsLength; i++) {
          ships.add(null);
        }
      }
    }
    for (var i = 0; i < shipsLength; i++) {
      var ship = shipMap[data["ship_ids"][i]];
      // Do not update the ObservableList if the value is the same.
      if (ships[i] != ship) {
        ships[i] = ship;
      }
    }
    if (data["mission_id"] != null) {
      undertakingMission = "不明";
      var missionId = data["mission_id"];
      for (var mission in missions) {
        if (mission.id == missionId) {
          undertakingMission = mission.name;
          missionEtaDatetimeString = mission.etaDatetimeString;
          break;
        }
      }
    } else {
      undertakingMission = null;
    }
    canWarmUp = ships.any((Ship ship) {
      return !ship.isUnderRepair &&
          ship.stateClass != "fatal" &&
          ship.stateClass != "dangerous" &&
          ship.vitality < WARMUP_VITALITY;
    });
    if (collapsed != null) {
      this.collapsed = collapsed;
    } else {
      this.collapsed = id != 1;
    }
  }
}

class FleetDeployment extends Observable {
  @observable String name;
  @observable ShipPredicate globalPredicate;
  @observable final List<ShipRequirement> shipRequirements =
      new ObservableList<ShipRequirement>();

  FleetDeployment(this.name, this.globalPredicate);

  FleetDeployment.fromShips(this.name, Iterable<Ship> ships) {
    globalPredicate = new ShipPredicate.fromTRUE();
    for (var ship in ships) {
      var predicate = new ShipPredicate.fromPropertyFilter(
          new ShipPropertyFilter.shipId(ship.id));
      var sorter = new ShipSorter.level(false);
      var omittable = false;
      shipRequirements.add(new ShipRequirement(predicate, sorter, omittable));
    }
    // Add padding up to 6 ships.
    for (var i = ships.length; i < 6; i++) {
      var predicate = new ShipPredicate.fromFALSE();
      var sorter = new ShipSorter.level(false);
      var omittable = true;
      shipRequirements.add(new ShipRequirement(predicate, sorter, omittable));
    }
  }

  FleetDeployment.fromJSON(Map<String, dynamic> data) {
    name = data["name"];
    globalPredicate = new ShipPredicate.fromJSON(data["global_predicate"]);
    for (var shipRequirement in data["ship_requirements"]) {
      shipRequirements.add(new ShipRequirement.fromJSON(shipRequirement));
    }
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "name": name,
      "global_predicate": globalPredicate.toJSONEncodable(),
      "ship_requirements": shipRequirements
          .map((shipRequirement) => shipRequirement.toJSONEncodable())
          .toList(),
    };
  }
}

class CombinedFleetDeployment extends Observable {
  @observable String name;
  @observable String primaryFleetName;
  @observable String secondaryFleetName;
  @observable int combinedFleetType;
  @observable String escotingFleetName;
  @observable String supportingFleetName;

  CombinedFleetDeployment(this.name, this.primaryFleetName,
      this.secondaryFleetName, this.escotingFleetName,
      this.supportingFleetName);

  CombinedFleetDeployment.fromJSON(Map<String, dynamic> data) {
    name = data["name"];
    primaryFleetName = data["primary_fleet_name"];
    secondaryFleetName = data["secondary_fleet_name"];
    combinedFleetType = data["combined_fleet_type"];
    escotingFleetName = data["escoting_fleet_name"];
    supportingFleetName = data["supporting_fleet_name"];
  }

  Map<String, dynamic> toJSONEncodable() {
    return {
      "name": name,
      "primary_fleet_name": primaryFleetName,
      "secondary_fleet_name": secondaryFleetName,
      "combined_fleet_type": combinedFleetType,
      "escoting_fleet_name": escotingFleetName,
      "supporting_fleet_name": supportingFleetName,
    };
  }
}
