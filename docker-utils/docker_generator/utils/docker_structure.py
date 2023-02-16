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
        'volumes': './influxdb/data:/var/lib/influxdb',
        'ipv4_address': '172.20.0.3'
    },
    'grafana': {
        'image': 'grafana/grafana:latest',
        'container_name': 'grafana',
        'restart': 'always',
        'ports': "3000:3000",
        'env_file': './grafana/env.grafana',
        'links': "influxdb",
        'volumes': './grafana/data:/var/lib/grafana',
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
    'traffic_predictor': {
        'image': 'python:3.8.12-slim',
        'container_name': 'traffic_predictor',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': ['./traffic_predictor:/etc/traffic_predictor/', './sumo-utils:/etc/sumo-utils/'],
        'command': 'bash -c "cd /etc/traffic_predictor && pip3 install -r requirements.txt && '
                   'cd t_predictor/ && dockerize -wait tcp://172.20.0.3:8086 -timeout 120s'
                   ' -wait-retry-interval 40s python3 ml_trainer.py --component -n 1'
                   ' --middleware_host 172.20.0.2 --middleware_port 1883"',
        'ipv4_address': '172.20.0.6'
    },
    'transportation_digital_twin': {
        'build': './transportation_digital_twin',
        'container_name': 'transportation_digital_twin',
        'env_file': 'transportation_digital_twin/eclipse-sumo-image/env.sumo',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': ['./transportation_digital_twin:/etc/transportation_digital_twin/', './sumo-utils:/etc/sumo-utils/',
                    '{}:{}', './traffic_predictor:/etc/traffic_predictor/',
                    './turn_predictor:/etc/turn_predictor/', './traffic_analyzer:/etc/traffic_analyzer/'],
        'command': 'bash -c "cd /etc/transportation_digital_twin && pip3 install -r requirements.txt && '
                   'cd tdt/ &&  dockerize -wait tcp://172.20.0.3:8086 -timeout 120s'
                   ' -wait-retry-interval 20s python3 {}"',
        'ipv4_address': '172.20.0.7'
        # TODO add load topology into the database. Not delete the container even if the process has finished
    },  # Added {} to parametrize execution
    'traffic_analyzer': {
        'image': 'python:3.8.12-slim',
        'container_name': 'traffic_analyzer',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': ['./traffic_analyzer:/etc/traffic_analyzer/', './sumo-utils:/etc/sumo-utils/'],
        'command': 'bash -c "cd /etc/traffic_analyzer && pip3 install -r requirements.txt && '
                   'cd t_analyzer/ && python3 main.py"',
        'ipv4_address': '172.20.0.8'
    },
    'neo4j': {
        'image': 'neo4j',
        'container_name': 'neo4j',
        'env_file': './neo4j/env.neo4j',
        'restart': 'always',
        'ports': ["7474:7474", "7687:7687"],
        'volumes': './neo4j:/etc/neo4j/',
        'ipv4_address': '172.20.0.9'
    },
    'exp_collector': {
        'image': 'python:3.8.12-slim',
        'container_name': 'exp_collector',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './exp_collector:/etc/exp_collector/',
        'command': 'bash -c "cd /etc/exp_collector && pip3 install -r requirements.txt && python3 main.py -o {} -w {}"',
        'ipv4_address': '172.20.0.11'
    },
    'turn_predictor': {
        'image': 'python:3.8.12-slim',
        'container_name': 'turn_predictor',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': ['./turn_predictor:/etc/turn_predictor/'],
        'command': 'bash -c "cd /etc/turn_predictor && pip3 install -r requirements.txt && '
                   'cd turns_predictor/ && dockerize -wait tcp://172.20.0.3:8086 -timeout 120s -wait-retry-interval '
                   '40s python3 ml_trainer.py --component -n 1 --middleware_host 172.20.0.2 --middleware_port 1883"',
        'ipv4_address': '172.20.0.12'
    }
}

DOCKER_EXECUTION_OPTIONS = {
    'transportation_digital_twin': {
        'pattern': 'main.py -c /etc/config/simulation.sumocfg --nogui -t {}',
        'date': 'main.py -c /etc/config/simulation.sumocfg --nogui -d {}'

    },
    'traffic_predictor': {
        'train': 'ml_trainer.py -t {} -c',
        'component': 'ml_trainer.py --component -n 1 --middleware_host 172.20.0.2 --middleware_port 1883'
    }
}
