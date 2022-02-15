#!/bin/sh

# Move to docker generator folder
cd ../../docker-utils/docker_generator || exit

# Clean up existing containers
../clean_up_containers.sh > /dev/null 2>&1

# Create docker-compose file with the time pattern
python main.py -o  ../../docker-compose.yml -c mosquitto,influxdb,telegraf

# Deploy the architecture
sudo docker-compose up
