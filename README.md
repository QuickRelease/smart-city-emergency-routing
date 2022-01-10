# Smart City Emergency Routing

Project completed by the ALTEN Labs Team for the ZF Hackathon 2022

## Instructions

1. Install [Python](https://www.python.org/), make sure you tick the box to add python to your system path during installation
2. Install [SUMO](https://sumo.dlr.de/wiki/Installing), make sure you tick the box to add SUMO to your system path during installation
3. Install the python dependencies via pip (e.g. `pip install -r requirements.txt`)
3. Run ./src/scenario_runner.py

## Scenarios

0 = Standard  
1 = With FORCING (traffic lights are forced green by the ambulance when approached)  
2 = With FORCING & BIASING (further away traffic lights get their phases biased to help reduce upcoming traffic)  
3 = With vehicles moving out of the way for the ambulance  
4 = With vehicles moving out of the way for the ambulance in advanced  

## Details

![image](https://user-images.githubusercontent.com/37864918/148594068-2ea7007e-6e9c-42db-95f0-930f4903aaa2.png)
![image](https://user-images.githubusercontent.com/37864918/148594096-0ab47daf-e2e0-41d0-a16f-15c948f1aaaf.png)

## Credits

Scenario runner skeleton and some of the maps based on https://github.com/sraddon/SUMO-V2X-Communication-Research-Platooning-and-CIM
