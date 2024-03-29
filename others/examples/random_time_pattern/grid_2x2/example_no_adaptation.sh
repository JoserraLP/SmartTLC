#!/bin/sh

cwd=$(pwd)/flows.rou.xml

# Move to docker generator folder
cd ../../../../docker-utils/docker_generator || exit

# Clean up existing containers
../clean_up_containers.sh > /dev/null 2>&1

# Create docker-compose file with the time pattern
python main.py -o  ../../docker-compose.yml -c mosquitto,influxdb,grafana,telegraf,traffic_light_controller:pattern#/etc/sumo-utils/time_patterns/random.csv:load#$cwd:rows#4:cols#4:lanes#2,exp_collector:exp_file#../exp_collector/2x2_random_time_pattern_no_adaptation.xlsx:waiting#1500

# Waiting time is 25 minutes (1500 seconds) per day simulated

# Deploy the architecture -> Build if changes
sudo docker-compose up --build
