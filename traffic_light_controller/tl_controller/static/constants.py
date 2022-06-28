# Proportions
TRAFFIC_PROPORTIONS = [0.25, 0.50, 1, 2, 4]

# Default number of programs is 5 (same as proportions)
TL_PROGRAMS = [f'static_program_{i+1}' for i in range(0, len(TRAFFIC_PROPORTIONS))]

# Bounds on phase time
LOWER_BOUND_TIME_PHASE = 20
UPPER_BOUND_TIME_PHASE = 70
MAXIMUM_TIME_PHASE = 80
MAXIMUM_TIME_BOUND_PHASE = UPPER_BOUND_TIME_PHASE - LOWER_BOUND_TIME_PHASE

MAXIMUM_TIME_PHASE_TURN = MAXIMUM_TIME_PHASE - 20

# Default date values
DEFAULT_DAY = "monday"
DEFAULT_DATE_DAY = "02"
DEFAULT_DATE_MONTH = "02"  # February
DEFAULT_DATE_YEAR = "2021"

# Timestep range for storing info into the dataset
TIMESTEPS_TO_STORE_INFO = 300  # 5 Cycles = 300 seconds
TIMESTEPS_PER_HALF_HOUR = 1800  # Half hour is 1800 seconds
TIMESTEPS_PER_MINUTE = 60

# Number of traffic types
NUM_TRAFFIC_TYPES = 11

# Options default values
DEFAULT_GUI_FLAG = False
DEFAULT_TURNS_FLAG = False
DEFAULT_NUMBER_OF_SIMULATIONS = 0
DEFAULT_CLI_VISUALIZE_FLAG = False
DEFAULT_CONFIG_FILE = '../../sumo-utils/output/simulation.sumocfg'

# Output directory where the flows will be stored
# FLOWS_OUTPUT_DIR = '../net-files/flows/flows.rou.xml'
FLOWS_OUTPUT_DIR = '../../sumo-utils/output/flows.rou.xml'

# Default time pattern file
DEFAULT_TIME_PATTERN_FILE = '../../sumo-utils/time_patterns/generated_calendar.csv'

# Default turn pattern
DEFAULT_TURN_PATTERN_FILE = '../../sumo-utils/time_patterns/base_patterns/turn_prob_patterns.csv'

# MQTT constants
MQTT_URL = '172.20.0.2'
MQTT_PORT = 1883
TRAFFIC_INFO_TOPIC = 'traffic_info'
PREDICTION_TOPIC = 'traffic_prediction'
ANALYSIS_TOPIC = 'traffic_analysis'

# Threshold for analyzer and prediction error
ERROR_THRESHOLD = 3

# Traffic Type VS TL Algorithm
# Based on TL interval study
'''
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
'''

# Based on TL proportion study
TRAFFIC_TYPE_TL_ALGORITHMS = {
    '0': 'static_program_3',
    '1': 'static_program_2',
    '2': 'static_program_4',
    '3': 'static_program_3',
    '4': 'static_program_2',
    '5': 'static_program_1',
    '6': 'static_program_4',
    '7': 'static_program_3',
    '8': 'static_program_2',
    '9': 'static_program_5',
    '10': 'static_program_4',
    '11': 'static_program_3',
}
