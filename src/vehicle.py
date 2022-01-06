import traci
from enum import Enum

from traci._trafficlight import Phase, Logic

TRAFFIC_LIGHT_FORCE_THRESHOLD = 30
TRAFFIC_LIGHT_BIAS_THRESHOLD = 1000
TRAFFIC_LIGHT_BIAS_MULTIPLIER = 150


class TrafficLightState(Enum):
    NONE = 1
    BIASED = 2
    FORCED = 3


def lane_to_edge(lane):
    return lane.split("_")[0]


class TrafficLight:

    def __init__(self, traffic_light_id, edge_from, edge_to):
        self.id = traffic_light_id
        self.edge_from = edge_from
        self.edge_to = edge_to
        self.current_distance = 0
        self.status = TrafficLightState.NONE
        self.original_logic = traci.trafficlight.getAllProgramLogics(self.id)[0]

    def force(self, vehicle_id, route_edge_pairs):
        self.status = TrafficLightState.FORCED
        print(f"FORCED: {self.id}")
        current_state = traci.trafficlight.getRedYellowGreenState(self.id)
        new_state = ""
        for i, link in enumerate(traci.trafficlight.getControlledLinks(self.id)):
            from_edge = lane_to_edge(link[0][0])
            to_edge = lane_to_edge(link[0][1])
            if (from_edge, to_edge) in route_edge_pairs:
                if current_state[i] == "G":
                    new_state = current_state
                    break
                new_state += "G"
            else:
                new_state += "r"
        traci.trafficlight.setRedYellowGreenState(self.id, new_state)
        # Prevent vehicle changing lanes now that we've changed the traffic lights
        traci.vehicle.setLaneChangeMode(vehicle_id, 0)

    def bias(self, vehicle_id, route_edge_pairs):
        print(f"BIASED: {self.id}")

        self.status = TrafficLightState.BIASED

        state_positions_on_route = set()
        for i, link in enumerate(traci.trafficlight.getControlledLinks(self.id)):
            from_edge = lane_to_edge(link[0][0])
            to_edge = lane_to_edge(link[0][1])
            if (from_edge, to_edge) in route_edge_pairs:
                # index i is on route
                state_positions_on_route.add(i)

        phases = []
        logic = traci.trafficlight.getAllProgramLogics(self.id)[0]
        for phase in logic.getPhases():
            good_phase = False
            for state_position in state_positions_on_route:
                if phase.state[state_position] == "G":
                    good_phase = True
                    break
            duration = phase.duration
            if good_phase:
                duration = duration * TRAFFIC_LIGHT_BIAS_MULTIPLIER
            phases.append(
                Phase(duration=duration, state=phase.state)
            )
        new_logic = Logic(
            programID=logic.programID,
            type=logic.type,
            currentPhaseIndex=logic.currentPhaseIndex,
            phases=phases,
        )
        print(new_logic)
        traci.trafficlight.setProgramLogic(self.id, new_logic)
        traci.trafficlight.setPhase(self.id, traci.trafficlight.getPhase(self.id))

    def clear(self, vehicle_id):
        print(f"CLEARED: {self.id}")
        self.status = TrafficLightState.NONE
        # print(f"I've passed Traffic Light {self.id}")
        traci.trafficlight.setProgramLogic(self.id, self.original_logic)
        traci.trafficlight.setProgram(self.id, 0)
        traci.trafficlight.setPhase(self.id, traci.trafficlight.getPhase(self.id))
        # Re-enable vehicle changing lanes now that we've gone through the traffic lights
        traci.vehicle.setLaneChangeMode(vehicle_id, 1621)


class Vehicle:
    def __init__(self, vehicle):
        self.id = vehicle
        self._route = traci.vehicle.getRoute(vehicle)
        self._route_edge_pairs = self.calculate_route_edge_pairs()
        self._traffic_lights_on_route = self.calculate_traffic_lights_on_route()

    def calculate_traffic_light_distances(self, traffic_light_lookahead):
        current_route = self._route
        current_route_index = traci.vehicle.getRouteIndex(self.id)
        current_lane = traci.vehicle.getLaneID(self.id)
        remaining_distance_on_current_edge = traci.lane.getLength(current_lane) - traci.vehicle.getLanePosition(self.id)
        edge_lengths = {
            edge_id: traci.lane.getLength(f"{edge_id}_0")
            for edge_id in current_route
        }
        for traffic_light in self._traffic_lights_on_route:
            traffic_light_index = current_route.index(traffic_light.edge_from)
            if traffic_light_index < current_route_index:
                # passed the TL already
                distance = -1
                if traffic_light.status is not TrafficLightState.NONE:
                    traffic_light.clear(self.id)
            else:
                distance = remaining_distance_on_current_edge
                for x in range(current_route_index + 1, traffic_light_index + 1):
                    distance += edge_lengths[current_route[x]]
            traffic_light.current_distance = distance
            if 0 <= traffic_light.current_distance < TRAFFIC_LIGHT_FORCE_THRESHOLD and traffic_light.status is not TrafficLightState.FORCED:
                traffic_light.force(self.id, self._route_edge_pairs)
            elif traffic_light_lookahead and TRAFFIC_LIGHT_FORCE_THRESHOLD <= traffic_light.current_distance < TRAFFIC_LIGHT_BIAS_THRESHOLD and traffic_light.status is TrafficLightState.NONE:
                traffic_light.bias(self.id, self._route_edge_pairs)

    def calculate_route_edge_pairs(self):
        edge_pairs = set()
        for i, edge in enumerate(self._route):
            if i == len(self._route) - 1:
                break
            edge_pairs.add((edge, self._route[i+1]))
        return edge_pairs

    def calculate_traffic_lights_on_route(self):
        traffic_lights_on_route = []
        traffic_light_ids = traci.trafficlight.getIDList()
        for traffic_light_id in traffic_light_ids:
            links = traci.trafficlight.getControlledLinks(traffic_light_id)
            for link in links:
                from_edge = lane_to_edge(link[0][0])
                to_edge = lane_to_edge(link[0][1])
                edge_pair = (from_edge, to_edge)
                if edge_pair in self._route_edge_pairs:
                    traffic_lights_on_route.append(TrafficLight(traffic_light_id, from_edge, to_edge))
                    break
        return traffic_lights_on_route



    def getAcceleration(self):
        return self._acceleration

    def isActive(self):
        return self._active

    def getEdge(self):
        return traci.vehicle.getRoadID(self.getName())

    def getLane(self):
        return traci.vehicle.getLaneID(self.getName())

    def getLaneIndex(self):
        return traci.vehicle.getLaneIndex(self.getName())

    def getLanePosition(self):
        return traci.vehicle.getLanePosition(self.getName())

    def getLanePositionFromFront(self):
        return traci.lane.getLength(self.getLane()) - self.getLanePosition()

    def getLeader(self):
        return traci.vehicle.getLeader(self.getName(), 20)

    def getLength(self):
        return self._length

    def getMaxSpeed(self):
        return self._maxSpeed

    def getName(self):
        return self.id

    def getRemainingRoute(self):
        return self._route[traci.vehicle.getRouteIndex(self.getName()) :]

    def getRoute(self):
        return self._route

    def getSpeed(self):
        return traci.vehicle.getSpeed(self.getName())

    def setColor(self, color):
        self._setAttr("setColor", color)

    def setInActive(self):
        self._active = False

    def setImperfection(self, imperfection):
        self._setAttr("setImperfection", imperfection)

    def setMinGap(self, minGap):
        self._setAttr("setMinGap", minGap)

    def setTargetLane(self, lane):
        traci.vehicle.changeLane(self.getName(), lane, 0.5)

    def setTau(self, tau):
        self._setAttr("setTau", tau)

    def setSpeed(self, speed):
        self._setAttr("setSpeed", speed)

    def setSpeedMode(self, speedMode):
        self._setAttr("setSpeedMode", speedMode)

    def setSpeedFactor(self, speedFactor):
        self._setAttr("setSpeedFactor", speedFactor)

    def _setAttr(self, attr, arg):
        # Only set an attribute if the value is different from the previous value set
        # This improves performance
        if self.isActive():
            if attr in self._previouslySetValues:
                if self._previouslySetValues[attr] == arg:
                    return
            self._previouslySetValues[attr] = arg
            getattr(traci.vehicle, attr)(self.getName(), arg)
