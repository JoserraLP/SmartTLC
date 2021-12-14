#!/bin/sh
cd ../docker-utils/docker_generator && ../clean_up_containers.sh > /dev/null 2>&1; python main.py -o  ../../docker-compose.yml -c mosquitto,influxdb,grafana,telegraf,traffic_light_controller && sudo docker-compose up
