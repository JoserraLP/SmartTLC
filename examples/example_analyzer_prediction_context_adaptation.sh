#!/bin/sh
cd ../docker-utils/docker_generator && ../clean_up_containers.sh > /dev/null 2>&1; python main.py -o  ../../docker-compose.yml -c mosquitto,influxdb,grafana,telegraf,traffic_light_controller,traffic_analyzer,traffic_light_predictor_context && sudo docker-compose up
