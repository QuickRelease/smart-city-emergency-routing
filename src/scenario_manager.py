import logging
import traci
from simulationmanager import SimulationManager
from simlib import setUpSimulation

from collections import namedtuple

scenarioNumberConfigTuple = namedtuple(
    "scenarioNumberConfig",
    "nameModifier enableManager level",
)
scenarioMapConfigTuple = namedtuple(
    "scenarioMapConfig",
    "mapName defaultTrafficScale initialZoom initialX initialY cutZoom ambulanceStartStep ambulanceStartEdge ambulanceEndEdge forceThreshold biasThreshold biasMultiplier"
)

DEFAULT_OUTPUT_SAVE_LOCATION = "output/additional.xml"

SCENARIO_NUMBER_CONFIGS = {
    0: scenarioNumberConfigTuple("", False, 0),
    1: scenarioNumberConfigTuple("", True, 1),
    2: scenarioNumberConfigTuple("", True, 2),
}

SCENARIO_LOCATION_CONFIG = {
    "Blackwell": scenarioMapConfigTuple("BlackwellTunnelNorthApproach", 1, 310.461, 432.022, 1352.41, 1200, 80, "NewIn", "A12NorthOut", 60, 300, 0.5),
    "Intersection": scenarioMapConfigTuple("NormalIntersection", 3, 484.915, 108.796, 100.417, 677.369, 20, "leftin", "rightout", 60, 1000, 0.5),
    "Roundabout": scenarioMapConfigTuple("A13NorthCircularRoundabout", 1, 131.666, 851.572, 920.085, 550, 100, "NCSouthIn", "A13EastOut", 60, 1000, 0.5),
    "London": scenarioMapConfigTuple("London", 1, 256.579, 3229.19, 1916.58, 3057.95, 3, "-564865636#0", "100077167#2", 60, 1000, 0.5),
}


def runScenario(mapName, scenarioNum, numOfSteps=20000):
    """Runs a given scenario using the given scenario name and number."""
    logging.info("Starting scenario for (name: %s | number: %s)")
    # Get config information
    scenarioLocationConfig = SCENARIO_LOCATION_CONFIG.get(mapName)
    scenarioNumberConfig = SCENARIO_NUMBER_CONFIGS.get(scenarioNum)
    if not scenarioLocationConfig:
        raise ValueError(
            "Could not find a scenario for the given name %s, available names: %s"
            % (mapName, SCENARIO_LOCATION_CONFIG.keys())
        )
    if not scenarioNumberConfig:
        raise ValueError(
            "Could not find a scenario for the given number %s, available numbers: %s"
            % (scenarioNum, SCENARIO_NUMBER_CONFIGS.keys())
        )

    baseScenarioName = scenarioLocationConfig.mapName
    logging.info(
        "Got map name %s and number config %s",
        baseScenarioName,
        "|".join(
            [
                " %s: %s " % (key, value)
                for key, value in scenarioNumberConfig._asdict().items()
            ]
        ),
    )
    mapName = baseScenarioName + scenarioNumberConfig.nameModifier

    # Get location of config files and place to store the output
    currPath = __file__.replace("\\", "/")
    mainProjectDirectory = "/".join(
        currPath.split("/")[: currPath.split("/").index("src")]
    )
    mapLocation = "{0}/maps/{1}/{1}.sumocfg".format(mainProjectDirectory, mapName)
    outputFileLocation = "{0}/{1}".format(
        mainProjectDirectory, DEFAULT_OUTPUT_SAVE_LOCATION
    )

    setUpSimulation(
        mapLocation, scenarioLocationConfig.defaultTrafficScale, outputFileLocation
    )
    step = 0
    manager = (
        SimulationManager(
            level=scenarioNumberConfig.level,
            force_threshold=scenarioLocationConfig.forceThreshold,
            bias_threshold=scenarioLocationConfig.biasThreshold,
            bias_multiplier=scenarioLocationConfig.biasMultiplier,
        )
        if scenarioNumberConfig.enableManager
        else None
    )

    view_name = "View #0"

    traci.gui.setZoom(view_name, scenarioLocationConfig.initialZoom)
    traci.gui.setOffset(view_name, scenarioLocationConfig.initialX, scenarioLocationConfig.initialY)

    while step < numOfSteps:
        if scenarioLocationConfig.ambulanceStartStep and scenarioLocationConfig.ambulanceStartStep == traci.simulation.getTime():
            traci.route.add("ambulance_route", [scenarioLocationConfig.ambulanceStartEdge, scenarioLocationConfig.ambulanceEndEdge])
            traci.vehicle.add(vehID="ambulance", routeID="ambulance_route", typeID="ambulance", departSpeed="max")
            traci.gui.setZoom(view_name, scenarioLocationConfig.cutZoom)
            traci.gui.trackVehicle(view_name, "ambulance")
        if manager:
            manager.handleSimulationStep()
        traci.simulationStep()
        step += 1

    traci.close()
