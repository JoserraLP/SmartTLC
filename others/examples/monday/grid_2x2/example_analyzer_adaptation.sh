#!/bin/sh

cwd=$(pwd)/flows.rou.xml

# Move to docker generator folder
cd ../../../../docker-utils/docker_generator || exit

# Clean up existing containers
../clean_up_containers.sh > /dev/null 2>&1 

# Create docker-compose file with the time pattern
python main.py -o  ../../docker-compose.yml -c traffic_analyzer,mosquitto,influxdb,grafana,telegraf,traffic_light_controller:pattern#/etc/traffic_light_controller/time_patterns/base_patterns/monday.csv:load#$cwd:rows#4:cols#4:lanes#2,exp_collector:exp_file#../exp_collector/2x2_one_day_analyzer.xlsx:waiting#1500

# Deploy the architecture
sudo docker-compose up
