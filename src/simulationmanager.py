import traci

from vehicle import Vehicle


class SimulationManager:
    def __init__(self):
        self.emergency_vehicles = {}

    def handleSimulationStep(self):
        allVehicles = traci.vehicle.getIDList()

        for vehicle_id in allVehicles:
            if traci.vehicle.getTypeID(vehicle_id) == "ambulance" and not vehicle_id in self.emergency_vehicles:
                self.emergency_vehicles[vehicle_id] = Vehicle(vehicle_id)

        vehicle_ids_to_delete = []

        for vehicle_id, emergency_vehicle in self.emergency_vehicles.items():
            if not vehicle_id in allVehicles:
                vehicle_ids_to_delete.append(vehicle_id)
            else:
                emergency_vehicle.calculate_traffic_light_distances()

        for vehicle_id in vehicle_ids_to_delete:
            del self.emergency_vehicles[vehicle_id]
