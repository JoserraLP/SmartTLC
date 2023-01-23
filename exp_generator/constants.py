CALENDAR_PATTERN_FILE = '../sumo-utils/time_patterns/generated_calendar.csv'

ADAPTATION_APPROACHES = {
    'no_adaptation': '',
    'analyzer_no_turn_adaptation': ';traffic-analyzer#all',
    'analyzer_turn_adaptation': ';traffic-analyzer#all;turn-predictor#all',
    'traffic_predictor_no_turn_adaptation': ';traffic-predictor#all',
    'traffic_predictor_turn_adaptation': ';traffic-predictor#all;turn-predictor#all',
    'traffic_predictor_analyzer_no_turn_adaptation': ';traffic-predictor#all;traffic-analyzer#all',
    'traffic_predictor_analyzer_turn_adaptation': ';traffic-predictor#all;turn-predictor#all;traffic-analyzer#all',
}

ADAPTATION_FILE_SCHEMA = '#!/bin/sh \n\
\n\
cwd=$(pwd)/config/flows.rou.xml\n\
\n\
## Move to docker generator folder \n\
cd {num_parent_folders}docker-utils/docker_generator || exit \n\
\n\
## Clean up existing containers \n\
../clean_up_containers.sh > /dev/null 2>&1 \n\
\n\
## Create docker-compose file with the time pattern \n\
python main.py -o  ../../docker-compose.yml -c mosquitto,influxdb,grafana,telegraf,\
transportation_digital_twin;{tlc_pattern};load#$cwd;rows#{rows};cols#{cols};lanes#{lanes}{tl_components},\
exp_collector;exp_file#{exp_file};waiting#{time}{db_url}{add_components} \n\
\n\
## Waiting time is 25 minutes (1500 seconds) per day simulated \n\
\n\
## Deploy the architecture\n\
sudo docker-compose up\n'

DEFAULT_CONFIG_GENERATOR_SCRIPT = "../sumo-utils/sumo_generators/grid_topology_generator.py"

# WINDOWS
WINDOWS_START = "@echo off"
WINDOWS_CUR_DIR = 'SET cwd=%cd%'
WINDOWS_COMMENT = ':'
WINDOWS_SLASH = '\\'
WINDOWS_VARIABLE = '%cwd%'
WINDOWS_ECHO_NULL = ''

# UBUNTU
UBUNTU_START = "#!/bin/sh"
UBUNTU_CUR_DIR = 'cwd=$(pwd)'
UBUNTU_COMMENT = '##'
UBUNTU_SLASH = '/'
UBUNTU_VARIABLE = '$cwd'
UBUNTU_ECHO_NULL = "> /dev/null 2>&1"
