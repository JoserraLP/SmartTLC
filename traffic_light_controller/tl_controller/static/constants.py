# Flows variables and its values
FLOWS_VALUES = {
    'high': {
        'vehsPerHour': 500,
        'vehs_range': 150
    },
    'med': {
        'vehsPerHour': 150,
        'vehs_range': 45
    },
    'low': {
        'vehsPerHour': 20,
        'vehs_range': 6
    },
    'very_low': {
        'vehsPerHour': 3,
        'vehs_range': 2
    }
}

# Output directory where the flows will be stored
FLOWS_OUTPUT_DIR = '../net-files/flows/flows.rou.xml'

# All the possible TL programs
# TL_PROGRAMS = ['static_program', 'actuated_program', 'actuated_program_time_gap', 'actuated_program_time_loss']
TL_PROGRAMS = [f'static_program_{i}' for i in range(1, 14)]


# Timestep range for storing info into the dataset
TIMESTEPS_TO_STORE_INFO = 300  # 5 Cycles = 300 seconds
TIMESTEPS_PER_HALF_HOUR = 1800  # Half hour is 1800 seconds
TIMESTEPS_PER_MINUTE = 60

# Number of traffic types
NUM_TRAFFIC_TYPES = 11

# Options default values
DEFAULT_GUI_FLAG = False
DEFAULT_NUMBER_OF_SIMULATIONS = 0
DEFAULT_CLI_VISUALIZE_FLAG = False
DEFAULT_CONFIG_FILE = '../net-files/config/simulation.sumocfg'
DEFAULT_OUTPUT_FILE = '../output/simulation.csv'

# Default time pattern file
DEFAULT_TIME_PATTERN_FILE = '../time_patterns/calendar.csv'

# MQTT constants
MQTT_URL = '172.20.0.2'
MQTT_PORT = 1883
TRAFFIC_INFO_TOPIC = 'traffic_info'
PREDICTION_TOPIC = 'traffic_prediction'

# Threshold for analyzer and prediction error
ERROR_THRESHOLD = 3

# Traffic Type VS TL Algorithm
TRAFFIC_TYPE_TL_ALGORITHMS = {
    '0': 'static_program_7',
    '1': 'static_program_1',
    '2': 'static_program_10',
    '3': 'static_program_8',
    '4': 'static_program_2',
    '5': 'static_program_1',
    '6': 'static_program_12',
    '7': 'static_program_5',
    '8': 'static_program_2',
    '9': 'static_program_13',
    '10': 'static_program_12',
    '11': 'static_program_5',
}