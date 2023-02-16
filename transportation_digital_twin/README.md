#  Transportation Digital Twin
It is the component that will simulate the traffic time patterns and perform the traffic light adaptation based on the
Traffic Light Adapter sub-component (described below). The default behavior of the traffic light algorithms is an 
equally distributed algorithm with 40 seconds of green phase and 5 seconds on amber phase per direction. This component 
retrieve contextual information (waiting time and number of vehicles passing per lane) from the traffic simulation each 
hour.  

It is important to mention that each traffic light monitors its contextual information individually and publish it into 
the middleware, each one of them having its own adapter. Additionally, each traffic light can have a traffic analyzer,
a traffic predictor and a turn predictor.

## Usage
The execution command for this component is the following one:
```sh
# Simulation with dates from 01/01/2021 to 02/01/2021 
python main.py --nogui --dates 01/01/2021-02/01/2021

# Simulation with a given time pattern (Monday)
python main.py --nogui --time-pattern ../time_patterns/base_patterns/monday.csv
```

Where the parameters are, grouped by functionality:
-  **-h, --help**: show this help message and exit.
- **Simulation options**:
  - **--nogui**: flag to use either the SUMO GUI or not in the simulation process. By default, is set to *True*, which 
  means that the GUI is not used.
  - **-c CONFIG_FILE, --config CONFIG_FILE**: sumo configuration file location. 
  Default is ../../sumo-utils/config/simulation.sumocfg
  - **-t FILE, --time-pattern FILE**: time pattern input file. Do not use it with the "dates" parameter.
  - **-d DATES, --dates DATES**: calendar dates from start to end to simulate. Format is dd/mm/yyyy-dd/mm/yyyy.
  - **-l LOAD_VEHICLES_DIR, --load-vehicles LOAD_VEHICLES_DIR**: directory from where the vehicles routes 
  will be load. Default to False.
  - **--temporal-window TEMPORAL_WINDOW**: temporal window used to gather contextual information and adaptation process.
  It is represented as number of traffic lights cycles. Default to 5 cycles.
- **Middleware options**:
  - **--middleware-host MQTT_URL**: middleware broker host. Default is 172.20.0.2
  - **--middleware-port MQTT_PORT**: middleware broker port. Default is 1883
  - **--local**: run the component locally. It will not connect to middleware.
- **Traffic Light additional component options**:
  - **--traffic-analyzer TRAFFIC_ANALYZER**: enable traffic analyzer on traffic lights. 
  Can be 'all' or the names of the traffic lights split by ','.
  - **--turn-predictor TURN_PREDICTOR**: enable turn predictor on traffic lights. 
  Can be 'all' or the names of the traffic lights split by ','.
  - **--traffic-predictor TRAFFIC_PREDICTOR**: enable traffic predictor on traffic lights. 
  Can be 'all' or the names of the traffic lights split by ','.
- **Network topology database options**:
  - **--topology-db-ip TOPOLOGY_DB_IP**: topology database ip address with port. Default to 172.20.0.9:7687
  - **--topology-db-user TOPOLOGY_DB_USER**: topology database user. Default to neo4j
  - **--topology-db-password TOPOLOGY_DB_PASSWORD**: topology database user password. Default to admin
  

Note that the time pattern and dates are indicated in the deployment scripts with the characters ":" and "#".

## Data model
The followed schema to publish the contextual traffic light information into the middleware is dictionary related to 
each traffic light and its lanes:
- **tl_id**: lane-related traffic light identifier. 
- **lane**: name of the lane where the info is published.
- **waiting_time_veh**: amount of waiting time (in seconds) in the lane.
- **num_passing_veh**: number of vehicles that has passed the lane.
- **avg_lane_occupancy**: average of the lane occupancy.
- **avg_CO2_emission**: average of CO2 emissions on the lane.
- **avg_CO_emission**: average of CO emissions on the lane.
- **avg_HC_emission**: average of HC emissions on the lane.
- **avg_PMx_emission**: average of PMx emissions on the lane.
- **avg_NOx_emission**: average of NOx emissions on the lane.
- **avg_noise_emission**: average of noise emissions on the lane.

Besides, the topic used to publish this information is "traffic_info/<traffic_light_id>" where *<traffic_light_id>* is 
the identifier of the traffic light that publishes the information. 

#  Traffic Light Adapter
This component is related to the adaptation process of the traffic light algorithms based on the topology and the 
additional components that a traffic light can have: Traffic predictor, Traffic analyzer and Turn predictor.

Additionally to these components, there are also defined different adaptation strategies that can be replaced runtime.
These strategies will use the information provided by those components or external information sources.

This component follows the **strategy pattern**.