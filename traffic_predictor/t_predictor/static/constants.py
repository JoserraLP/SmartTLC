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
TL_PROGRAMS = ['static_program', 'actuated_program', 'actuated_program_time_gap', 'actuated_program_time_loss']

# Timestep range for storing info into the dataset
TIMESTEPS_TO_STORE_INFO = 1800  # Equal to 30 minutes

# Number of traffic types
NUM_TRAFFIC_TYPES = 11

# Options default values
DEFAULT_GUI_FLAG = False
DEFAULT_NUMBER_OF_SIMULATIONS = 0
DEFAULT_CLI_VISUALIZE_FLAG = False
DEFAULT_CONFIG_FILE = '../net-files/config/simulation.sumocfg'
DEFAULT_OUTPUT_FILE = '../output/simulation_calendar.csv'

# Default time pattern file
DEFAULT_TIME_PATTERN_FILE = '../time_patterns/calendar.csv'

# Default calendar csv file
DEFAULT_CALENDAR_FILE = '../time_patterns/calendar.csv'

# Default output generated calendar csv file
DEFAULT_GENERATED_CALENDAR_FILE = '../time_patterns/generated_calendar.csv'

# Translate the days
TRANSLATE_DICT = {
    'lunes': 'monday',
    'martes': 'tuesday',
    'miercoles': 'wednesday',
    'miércoles': 'wednesday',
    'jueves': 'thursday',
    'viernes': 'friday',
    'sabado': 'saturday',
    'sábado': 'saturday',
    'domingo': 'sunday',
    'festivo': 'festive',
    'Festivo': 'festive',
    'laborable': 'working'
}

# Random ranges for noise generation on calendar
# Variance for vacation swap
RANDOM_VACATION_SWAP_RANGE = 15  # 15 days
# Variance for traffic type
RANDOM_TRAFFIC_TYPE_LOWER_BOUND = -2
RANDOM_TRAFFIC_TYPE_UPPER_BOUND = 2
RANDOM_TRAFFIC_TYPE_RANGE = 48 * 3  # 48 rows per 3 days
# Variance for vacations day swap to usual
RANDOM_VACATION_TO_USUAL_DAY_RANGE = 15  # 15 days
# Variance for usual day swap to vacation
RANDOM_USUAL_TO_VACATION_DAY_RANGE = 50  # 50 days
# Variance for usual day
RANDOM_USUAL_REPLACE = 14  # 14 days

# ML constants
KNN_MAX_NEIGHBORS = 15
DT_MAX_DEPTH = 20
RF_NUM_ESTIMATORS = 20
RF_MAX_DEPTH = 10
MODEL_BASE_DIR_CONTEXT = '../classifier_models_context/'
MODEL_BASE_DIR_DATE = '../classifier_models_date/'
MODEL_PERFORMANCE_FILE_CONTEXT = '../classifier_models_context/ml_performance.json'
MODEL_PERFORMANCE_FILE_DATE = '../classifier_models_date/ml_performance.json'
MODEL_PARSED_VALUES_FILE = '../output/parsed_values_dict.json'
DEFAULT_NUM_MODELS = 1
MODEL_NUM_FOLDS = 2

# MQTT constants
MQTT_URL = '172.20.0.2'
MQTT_PORT = 1883
TRAFFIC_INFO_TOPIC = 'traffic_info'
PREDICTION_TOPIC = 'traffic_prediction'
