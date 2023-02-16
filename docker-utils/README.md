# Docker utils
Library for generating a "docker-compose.yml" file based on pre-defined containers related to the SmartTLC framework. Besides, in this folder there are several *bash* and *sh* files related the cleanup, removal and stop of the Docker containers.

One of the most relevant features of this generator is that it uses a *dependency graph* in order to be aware of all 
the container dependencies existent in the framework, generating them even though the user has not selected them or has 
forgotten about it.

## Installation
In order to use this library, it is required to execute the following command in the root folder, where it is located 
the file "setup.py".

```sh
pip install -e .
```

## Usage
The execution itself of the library utils is performed by executing the next command, in the "docker_generator" folder:

```sh
python main.py <parameters>
```

This execution process generates a file where there are specified all the selected container following the 
Docker-compose specification.

Where the parameters defined are:

- **-h, --help**: show this help message and exit.
- **-o OUTPUT, --output-dir OUTPUT**: define the output directory where the output file will be stored. 
  Default is *./docker_compose.yml*.
- **-c CONTAINERS, --containers CONTAINERS**: containers to be generated on the Docker specification files, split by a comma ",". 
  Default values are: *mosquitto,influxdb,grafana,telegraf,traffic_predictor_date,traffic_predictor_context,
  transportation_digital_twin,traffic_analyzer,player,recorder,exp_collector*.
  
## Containers
All the available containers are:
- **mosquitto**: *middleware* component (Eclipse Mosquitto).
- **influxdb**: *data storage* component (InfluxDB).
- **grafana**: *data visualizer* component (Grafana).
- **telegraf**: *data consumer* component (Telegraf).
- **traffic_predictor**: *traffic type predictor* component.
- **transportation_digital_twin**: *transportation digital twin* component (Eclipse SUMO).
- **traffic_analyzer**: *traffic analyzer* component.
- **neo4j**: *network topology database* component (Neo4j).
- **exp_collector**: not related to any framework component but to an external component that collects information about
  a given experiment.
- **turn_predictor**: *turn predictor* component.


Additionally, it is also possible to specify different parameters per each container with the following schema:
```
<container_name>;<param_name>#<param_value>
```