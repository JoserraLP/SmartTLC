CALENDAR_PATTERN_FILE = '../sumo-utils/time_patterns/generated_calendar.csv'

ADAPTATION_COMPONENTS = {
    'no_adaptation': '',
    'analyzer_adaptation': ',traffic_analyzer',
    'prediction_date_adaptation': ',traffic_light_predictor_date',
    'analyzer_predictor_adaptation': ',traffic_light_predictor_context,traffic_analyzer'
}

ADAPTATION_FILE_SCHEMA = '#!/bin/sh \n\
\n\
cwd=$(pwd)/flows.rou.xml \n\
\n\
# Move to docker generator folder \n\
cd {num_parent_folders}docker-utils/docker_generator || exit \n\
\n\
# Clean up existing containers \n\
../clean_up_containers.sh > /dev/null 2>&1 \n\
\n\
# Create docker-compose file with the time pattern \n\
python main.py -o  ../../docker-compose.yml -c mosquitto,influxdb,grafana,telegraf,\
traffic_light_controller:{tlc_pattern}:load#$cwd:rows#{rows}:cols#{cols}:lanes#{lanes},\
exp_collector:exp_file#{exp_file}:waiting#4500{add_components} \n\
\n\
# Waiting time is 25 minutes (1500 seconds) per day simulated \n\
\n\
# Deploy the architecture\n\
sudo docker-compose up\n'
