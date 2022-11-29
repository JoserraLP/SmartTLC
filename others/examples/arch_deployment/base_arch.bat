@echo off

: Move to docker generator folder
cd ..\..\..\docker-utils\docker_generator || exit

: Create docker-compose file with the time pattern
python main.py -o  ..\..\docker-compose.yml -c mosquitto,influxdb,telegraf

: Deploy the architecture
docker-compose up

