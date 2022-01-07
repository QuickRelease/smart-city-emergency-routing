import traci

from vehicle import Vehicle


class SimulationManager:
    def __init__(self, level, force_threshold, bias_threshold, bias_multiplier):
        self.emergency_vehicles = {}
        self.level = level
        self.bias_mode = self.level == 2
        self.force_threshold = force_threshold
        self.bias_threshold = bias_threshold
        self.bias_multiplier = bias_multiplier

    def handleSimulationStep(self):
        allVehicles = traci.vehicle.getIDList()

        for vehicle_id in allVehicles:
            if traci.vehicle.getTypeID(vehicle_id) == "ambulance" and not vehicle_id in self.emergency_vehicles:
                self.emergency_vehicles[vehicle_id] = Vehicle(vehicle_id, self.bias_mode)

        vehicle_ids_to_delete = []

        for vehicle_id, emergency_vehicle in self.emergency_vehicles.items():
            if not vehicle_id in allVehicles:
                vehicle_ids_to_delete.append(vehicle_id)
            else:
                emergency_vehicle.calculate_traffic_light_distances(
                    force_threshold=self.force_threshold,
                    bias_threshold=self.bias_threshold,
                    bias_multiplier=self.bias_multiplier,
                )

        for vehicle_id in vehicle_ids_to_delete:
            del self.emergency_vehicles[vehicle_id]
