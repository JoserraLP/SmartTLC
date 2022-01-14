#!/bin/sh

# Move to docker generator folder
cd ../../docker-utils/docker_generator || exit

# Clean up existing containers
../clean_up_containers.sh > /dev/null 2>&1

# Create docker-compose file with date range
python main.py -o  ../../docker-compose.yml -c mosquitto,influxdb,grafana,telegraf,traffic_light_controller:date#18/07/2021-20/07/2021,traffic_light_predictor_date 

# Deploy the architecture
sudo docker-compose up