# Smart City Emergency Routing

Project created for ZF Hackathon 2022

## Instructions

1. Install [Python](https://www.python.org/), make sure you tick the box to add python to your system path during installation
2. Install [SUMO](https://sumo.dlr.de/wiki/Installing), make sure you tick the box to add SUMO to your system path during installation
3. Run ./src/scenario_runner.py

## Scenarios

0 = Standard  
1 = With FORCING (traffic lights are forced green by the ambulance when approached)  
2 = With FORCING & BIASING (further away traffic lights get their phases biased to help reduce upcoming traffic)  
3 = With vehicles moving out of the way for the ambulance  
4 = With vehicles moving out of the way for the ambulance in advanced  
