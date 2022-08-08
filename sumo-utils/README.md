# SUMO utils
Library for generating several configuration files related to Eclipse SUMO. Its main features of are:
- Grid network generation
- Traffic light algorithms generation
- Network detectors generation
- Time pattern flows generation
- Eclipse SUMO configuration generation

All these features and its parameters are described below, along with its parameters.

## Installation
In order to execute this library, it is required to execute the following command in the root folder, 
where it is located the file "setup.py".

```sh
pip install -e .
```

## Usage
The execution itself of the library utils is performed by executing the next command, in the "sumo_generators' folder:

```sh
python config_generator.py <parameters>
```

This execution process generates the following files:
- Detectors file.
- Full network file.
    - Network edges file.
    - Network nodes file.
- SUMO simulation configuration file.
- Time pattern flows file.
- Traffic light algorithms file.

Where the parameters defined are, grouped by its functionality:

-  **-h, --help**: show this help message and exit.

- **Output configuration files generator**:
    - **-n NODES_PATH, --nodes-path NODES_PATH**: define the path where the nodes file is created. Default is 
      *../output/topology.nod.xml*. 
    - **-e EDGES_PATH, --edges-path EDGES_PATH**: define the path where the edges file is created. Default is 
      *../output/topology.edg.xml*.
    - **-d DETECTOR_PATH, --detector-path DETECTOR_PATH**: detectors file location. Default is 
      *../output/topology.det.xml*.
    - **-t TL_PROGRAM_PATH, --tl-program-path TL_PROGRAM_PATH**: SUMO traffic lights programs file location. Default is 
      *../output/topology.tll.xml*.
    - **-o NETWORK_PATH, --output-network NETWORK_PATH**: define the path where the network file is created. Default is 
      *../output/topology.net.xml*.
    - **-f FLOWS_PATH, --flows-path FLOWS_PATH**: define the path where the flows file is created. Default is 
      *../output/flows.rou.xml*.
    - **-s SUMO_CONFIG_PATH, --sumo-config-path SUMO_CONFIG_PATH**: SUMO configuration file location. Default is
      *../output/simulation.sumocfg*.
- **Network generator**:
    - **-r ROWS, --rows ROWS**: define the number of rows of the network. Default is *1*.
    - **-c COLS, --cols COLS**: define the number of cols of the network. Default is *1*.
    - **-l LANES, --lanes LANES**: define the number of lanes per edge. Must be greater than 0. Default is *1*.
    - **--distance DISTANCE**: define the distance between the nodes. Must be greater than 0. Default is *500*. 
    - **-j JUNCTION, --junction JUNCTION**: define the junction type on central nodes. Possible types are: *priority*, 
      *traffic_light*, *right_before_left*, *priority_stop*, *allway_stop*, *traffic_light_right_on_red*.
      Default is *traffic_light*.
    - **--tl-type TL_TYPE**: define the tl type, only if the 'junction' value is 'traffic_light'. 
      Possible types are: *static*, *actuated*, *delay_based*. Default is *static*. 
    - **--tl-layout TL_LAYOUT**: define the tl layout, only if the 'junction' value is 'traffic_light'. Possible types 
      are: *opposites*, *incoming*, *alternateOneWay*. Default is *opposites*.

- **Traffic Light generator**:
  - **-i INTERVAL, --interval INTERVAL**: interval of seconds to be used in the traffic light generator. 
  - **-p, --proportion**: flag to use proportions in the traffic light generator.
  - **--allow-add-turn-phases**: flag allowing left turns in traffic light phases. Default to False.  
    
- **Flows generator**:
  - **time-pattern TIME_PATTERN_PATH**: define the path where the time pattern file is stored to create the flows.
  - **--dates DATES**: indicates the range of dates, retrieved from the generated calendar, that will be simulated. 
  The format is dd/mm/yyyy-dd/mm/yyyy, where the first date is the start, and the second one is the end, both included.
  
Note: in the script itself, all the parameters are grouped based on its functionality, but in this case
it is not shown here in order to clarify its reading. If you want to see these groups execute the script 
with the **-h** or **--help** argument.