#!/bin/sh

# Move to docker generator folder
cd ../../../docker-utils/docker_generator || exit

# Clean up existing containers
../clean_up_containers.sh > /dev/null 2>&1 

# Create docker-compose file with the time pattern
python main.py -o  ../../docker-compose.yml -c traffic_analyzer,mosquitto,influxdb,grafana,telegraf,traffic_light_controller:pattern#/etc/traffic_light_controller/time_patterns/random.csv

# Deploy the architecture
sudo docker-compose up
