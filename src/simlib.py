import logging
import traci
from sumolib import checkBinary


def flatten(l):
    # A basic function to flatten a list
    return [item for sublist in l for item in sublist]


def setUpSimulation(
    configFile, trafficScale=1, outputFileLocation="output/additional.xml"
, level=0):
    # Check SUMO has been set up properly
    sumoBinary = checkBinary("sumo-gui")

    # Set up logger
    logging.basicConfig(format="%(asctime)s %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    if level>2:
    # Start Simulation and step through
        traci.start(
            [
                sumoBinary,
                "-c",
                configFile,
                "--lateral-resolution",
                "2.5",
                "--step-length",
                "0.1",
                "--collision.action",
                "none",
                "--start",
                "--tripinfo-output",
                outputFileLocation,
                # "--additional-files",
                # outputFileLocation,
                "--duration-log.statistics",
                "--scale",
                str(trafficScale),
            ]
        )
    else:
        traci.start(
            [
                sumoBinary,
                "-c",
                configFile,
                "--step-length",
                "0.1",
                "--collision.action",
                "none",
                "--start",
                "--tripinfo-output",
                outputFileLocation,
                # "--additional-files",
                # outputFileLocation,
                "--duration-log.statistics",
                "--scale",
                str(trafficScale),
            ]
        )
