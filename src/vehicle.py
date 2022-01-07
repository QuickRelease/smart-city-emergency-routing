import traci
from enum import Enum

from traci._trafficlight import Phase, Logic


class TrafficLightState(Enum):
    NONE = 1
    BIASED = 2
    FORCED = 3


def lane_to_edge(lane):
    return lane.split("_")[0]


class TrafficLight:

    def __init__(self, traffic_light_id, edge_from, edge_to, advance_phase_on_clear=False):
        self.id = traffic_light_id
        self.edge_from = edge_from
        self.edge_to = edge_to
        self.current_distance = 0
        self.status = TrafficLightState.NONE
        self.original_logic = traci.trafficlight.getAllProgramLogics(self.id)[0]
        self.unfavourable_phase_id = 0
        self.advance_phase_on_clear = advance_phase_on_clear

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

    def bias(self, bias_multiplier, route_edge_pairs):
        print(f"BIASED: {self.id}")

        self.status = TrafficLightState.BIASED

        state_positions_on_route = set()
        for i, link in enumerate(traci.trafficlight.getControlledLinks(self.id)):
            # TODO: Remove this bare exception
            try:
                from_edge = lane_to_edge(link[0][0])
                to_edge = lane_to_edge(link[0][1])
                if (from_edge, to_edge) in route_edge_pairs:
                    # index i is on route
                    state_positions_on_route.add(i)
            except:
                pass

        phases = []
        logic = traci.trafficlight.getAllProgramLogics(self.id)[0]
        for phase in logic.getPhases():
            good_phase = False
            for state_position in state_positions_on_route:
                if phase.state[state_position] == "G":
                    good_phase = True
                    break
            duration = phase.duration
            if not good_phase:
                duration = duration * bias_multiplier
            phases.append(
                Phase(duration=duration, state=phase.state)
            )
        new_logic = Logic(
            programID=logic.programID,
            type=logic.type,
            currentPhaseIndex=logic.currentPhaseIndex,
            phases=phases,
        )
        traci.trafficlight.setProgramLogic(self.id, new_logic)
        traci.trafficlight.setPhase(self.id, traci.trafficlight.getPhase(self.id))

    def clear(self, vehicle_id):
        print(f"CLEARED: {self.id}")
        self.status = TrafficLightState.NONE
        # print(f"I've passed Traffic Light {self.id}")
        traci.trafficlight.setProgramLogic(self.id, self.original_logic)
        traci.trafficlight.setProgram(self.id, 0)
        # TODO: Handle if we're already on the last phase
        next_phase = traci.trafficlight.getPhase(self.id)
        if self.advance_phase_on_clear:
            next_phase += 1
        traci.trafficlight.setPhase(self.id, next_phase)
        # Re-enable vehicle changing lanes now that we've gone through the traffic lights
        traci.vehicle.setLaneChangeMode(vehicle_id, 1621)


class Vehicle:
    def __init__(self, vehicle, bias_mode):
        self.id = vehicle
        self.bias_mode = bias_mode
        self._route = traci.vehicle.getRoute(vehicle)
        self._route_edge_pairs = self.calculate_route_edge_pairs()
        self._traffic_lights_on_route = self.calculate_traffic_lights_on_route()

    def calculate_traffic_light_distances(self, force_threshold, bias_threshold, bias_multiplier):
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
            if 0 <= traffic_light.current_distance < force_threshold and traffic_light.status is not TrafficLightState.FORCED:
                traffic_light.force(self.id, self._route_edge_pairs)
            elif self.bias_mode and force_threshold <= traffic_light.current_distance < bias_threshold and traffic_light.status is TrafficLightState.NONE:
                traffic_light.bias(bias_multiplier, self._route_edge_pairs)

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
                    traffic_lights_on_route.append(TrafficLight(traffic_light_id, from_edge, to_edge, advance_phase_on_clear=self.bias_mode))
                    break
        return traffic_lights_on_route
