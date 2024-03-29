#!/bin/sh

cwd=$(pwd)/flows.rou.xml

# Move to docker generator folder
cd ../../../../docker-utils/docker_generator || exit

# Clean up existing containers
../clean_up_containers.sh > /dev/null 2>&1

# Create docker-compose file with the time pattern
python main.py -o  ../../docker-compose.yml -c mosquitto,influxdb,grafana,telegraf,traffic_light_controller:date#18/07/2021-20/07/2021:load#$cwd:rows#4:cols#4:lanes#2,traffic_predictor_date

# Deploy the architecture
sudo docker-compose up
