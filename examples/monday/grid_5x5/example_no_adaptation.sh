#!/bin/sh

# Move to docker generator folder
cd ../../../docker-utils/docker_generator || exit

# Clean up existing containers
../clean_up_containers.sh > /dev/null 2>&1

# Create docker-compose file with the time pattern
python main.py -o  ../../docker-compose.yml -c mosquitto,influxdb,grafana,telegraf,traffic_light_controller:pattern#/etc/sumo-utils/time_patterns/base_patterns/monday.csv:rows#7:cols#7:lanes#2

# Deploy the architecture -> Build if changes
sudo docker-compose up --build
