DEFAULT_ROUTE_DIR = '/etc/flows/flows.rou.xml'

ALL_CONTAINERS = {
    'mosquitto': {
        'image': 'eclipse-mosquitto:latest',
        'container_name': 'mosquitto',
        'restart': 'always',
        'ports': "1883:1883",
        'volumes': './mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf',
        'ipv4_address': '172.20.0.2'
    },
    'influxdb': {
        'image': 'influxdb:latest',
        'container_name': 'influxdb',
        'restart': 'always',
        'ports': "8086:8086",
        'env_file': 'influxdb/env.influxdb',
        'volumes': '/srv/docker/influxdb/data:/var/lib/influxdb',
        'ipv4_address': '172.20.0.3'
    },
    'grafana': {
        'image': 'grafana/grafana:latest',
        'container_name': 'grafana',
        'restart': 'always',
        'ports': "3000:3000",
        'env_file': 'grafana/env.grafana',
        'links': "influxdb",
        'volumes': '/srv/docker/grafana/data:/var/lib/grafana',
        'ipv4_address': '172.20.0.4'
    },
    'telegraf': {
        'image': 'telegraf:latest',
        'container_name': 'telegraf',
        'restart': 'always',
        'links': 'influxdb',
        'depends_on': 'influxdb',
        'volumes': './telegraf/telegraf.conf:/etc/telegraf/telegraf.conf',
        'ipv4_address': '172.20.0.5'
    },
    'traffic_predictor_date': {
        'build': './traffic_predictor',
        'container_name': 'traffic_predictor',
        'env_file': 'traffic_redictor/eclipse-sumo-image/env.sumo',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './traffic_predictor:/etc/traffic_predictor/',
        'command': 'bash -c "pip3 install -r /etc/traffic_predictor/requirements.txt && '
                   'cd /etc/traffic_predictor/t_predictor/ && dockerize -wait '
                   'tcp://172.20.0.3:8086 -timeout 120s -wait-retry-interval 40s python3 ml_trainer.py --component -n 1'
                   ' --middleware_host 172.20.0.2 --middleware_port 1883 -d"',
        'ipv4_address': '172.20.0.6'
    },
    'traffic_predictor_context': {
        'build': './traffic_predictor',
        'container_name': 'traffic_predictor',
        'env_file': 'traffic_predictor/eclipse-sumo-image/env.sumo',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './traffic_predictor:/etc/traffic_predictor/',
        'command': 'bash -c "pip3 install -r /etc/traffic_predictor/requirements.txt && '
                   'cd /etc/traffic_predictor/t_predictor/ && dockerize -wait '
                   'tcp://172.20.0.3:8086 -timeout 120s -wait-retry-interval 40s python3 ml_trainer.py --component -n 1'
                   ' --middleware_host 172.20.0.2 --middleware_port 1883"',
        'ipv4_address': '172.20.0.6'
    },
    'traffic_light_controller': {
        'build': './traffic_light_controller',
        'container_name': 'traffic_light_controller',
        'env_file': 'traffic_light_controller/eclipse-sumo-image/env.sumo',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': ['./traffic_light_controller:/etc/traffic_light_controller/', './sumo-utils:/etc/sumo-utils/',
                    '{}'+f':{DEFAULT_ROUTE_DIR}'],
        'command': 'bash -c "pip3 install -r /etc/traffic_light_controller/requirements.txt && '
                   'cd /etc/sumo-utils/sumo_generators && python3 config_generator.py {} && '
                   'cd /etc/traffic_light_controller/tl_controller/ &&  dockerize -wait '
                   'tcp://172.20.0.3:8086 -timeout 120s -wait-retry-interval 20s python3 {}"',
        'ipv4_address': '172.20.0.7'
    }, # Added {} to parametrize execution
    'traffic_analyzer': {
        'image': 'python:3.8.12-slim',
        'container_name': 'traffic_analyzer',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './traffic_analyzer:/etc/traffic_analyzer/',
        'command': 'bash -c "pip3 install -r /etc/traffic_analyzer/requirements.txt && '
                   'cd /etc/traffic_analyzer/t_analyzer/ && python3 main.py"',
        'ipv4_address': '172.20.0.8'
    },
    'player': {
        'image': 'python:3.8.12-slim',
        'container_name': 'player',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './player:/etc/player/',
        'command': 'bash -c "pip3 install -r /etc/player/requirements.txt && '
                   'cd /etc/player/ && python3 main.py -i {}"',
        'ipv4_address': '172.20.0.9'
    },
    'recorder': {
        'image': 'python:3.8.12-slim',
        'container_name': 'recorder',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './recorder:/etc/recorder/',
        'command': 'bash -c "pip3 install -r /etc/recorder/requirements.txt && '
                   'cd /etc/recorder/ && python3 main.py -o {}"',
        'ipv4_address': '172.20.0.10'
    },
    'exp_collector': {
        'image': 'python:3.8.12-slim',
        'container_name': 'exp_collector',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './exp_collector:/etc/exp_collector/',
        'command': 'bash -c "pip3 install -r /etc/exp_collector/requirements.txt && '
                   'cd /etc/exp_collector && python3 main.py -o {} -w {}"',
        'ipv4_address': '172.20.0.11'
    }
}

DOCKER_EXECUTION_OPTIONS = {
    'traffic_light_controller': {
        'pattern': 'main.py -c /etc/sumo-utils/output/simulation.sumocfg --nogui -t {}',
        'date': 'main.py -c /etc/sumo-utils/output/simulation.sumocfg --nogui -d {}'

    },
    'traffic_predictor': {
        'train_date': 'ml_trainer.py -t {} -c -d',
        'train_context': 'ml_trainer.py -t {} -c',
        'component_date': 'ml_trainer.py --component -n 1 --middleware_host 172.20.0.2 --middleware_port 1883 -d',
        'component_context': 'ml_trainer.py --component -n 1 --middleware_host 172.20.0.2 --middleware_port 1883'
    }
}