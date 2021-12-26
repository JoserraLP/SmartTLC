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
    'traffic_light_predictor_date': {
        'build': './traffic_light_predictor',
        'container_name': 'traffic_light_predictor',
        'env_file': 'traffic_light_predictor/eclipse-sumo-image/env.sumo',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './traffic_light_predictor:/etc/traffic_light_predictor/',
        'command': 'bash -c "pip3 install -r /etc/traffic_light_predictor/requirements.txt && '
                   'cd /etc/traffic_light_predictor/tl_predictor/ && dockerize -wait '
                   'tcp://172.20.0.3:8086 -timeout 100s -wait-retry-interval 20s python3 ml_trainer.py --component -n 1'
                   ' --middleware_host 172.20.0.2 --middleware_port 1883 -d"',
        'ipv4_address': '172.20.0.6'
    },
    'traffic_light_predictor_context': {
        'build': './traffic_light_predictor',
        'container_name': 'traffic_light_predictor',
        'env_file': 'traffic_light_predictor/eclipse-sumo-image/env.sumo',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './traffic_light_predictor:/etc/traffic_light_predictor/',
        'command': 'bash -c "pip3 install -r /etc/traffic_light_predictor/requirements.txt && '
                   'cd /etc/traffic_light_predictor/tl_predictor/ && dockerize -wait '
                   'tcp://172.20.0.3:8086 -timeout 100s -wait-retry-interval 20s python3 ml_trainer.py --component -n 1'
                   ' --middleware_host 172.20.0.2 --middleware_port 1883"',
        'ipv4_address': '172.20.0.6'
    },
    'traffic_light_controller': {
        'build': './traffic_light_controller',
        'container_name': 'traffic_light_controller',
        'env_file': 'traffic_light_controller/eclipse-sumo-image/env.sumo',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './traffic_light_controller:/etc/traffic_light_controller/',
        'command': 'bash -c "pip3 install -r /etc/traffic_light_controller/requirements.txt && '
                   'cd /etc/traffic_light_controller/tl_controller/ && dockerize -wait '
                   'tcp://172.20.0.3:8086 -timeout 100s -wait-retry-interval 20s python3 {}"',
        'ipv4_address': '172.20.0.7'
    },  # Added {} to parametrize execution
    'traffic_analyzer': {
        'image': 'python:3.8.12-slim',
        'container_name': 'traffic_analyzer',
        'restart': 'on-failure',
        'links': 'mosquitto',
        'volumes': './traffic_analyzer:/etc/traffic_analyzer/',
        'command': 'bash -c "pip3 install -r /etc/traffic_analyzer/requirements.txt && '
                   'cd /etc/traffic_analyzer/t_analyzer/ && python3 main.py"',
        'ipv4_address': '172.20.0.8'
    }

}

DOCKER_EXECUTION_OPTIONS = {
    'traffic_light_controller': {
        'monday': 'main.py --nogui -t /etc/traffic_light_controller/time_patterns/base_patterns/monday.csv',
        'tuesday': 'main.py --nogui -t /etc/traffic_light_controller/time_patterns/base_patterns/tuesday.csv'
    },
    'traffic_light_predictor': {
        'train_date': 'ml_trainer.py -t {} -c -d',
        'train_context': 'ml_trainer.py -t {} -c',
        'component_date': 'ml_trainer.py --component -n 1 --middleware_host 172.20.0.2 --middleware_port 1883 -d',
        'component_context': 'ml_trainer.py --component -n 1 --middleware_host 172.20.0.2 --middleware_port 1883'
    }
}
