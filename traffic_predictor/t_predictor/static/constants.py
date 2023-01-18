# Options default values
DEFAULT_OUTPUT_FILE = '../../sumo-utils/time_patterns/calendar_time_pattern.csv'

# Time patterns default folder
DEFAULT_BASE_TIME_PATTERNS_FOLDER = '../../sumo-utils/time_patterns/base_patterns/'

# Default calendar csv file
DEFAULT_CALENDAR_FILE = '../../sumo-utils/time_patterns/calendar.csv'

# Default output generated calendar csv file
DEFAULT_GENERATED_CALENDAR_FILE = '../../sumo-utils/time_patterns/generated_calendar.csv'

# Number of rows per day
NUM_ROWS_PER_DAY = 24

# Random ranges for noise generation on calendar
# Variance for vacation swap
RANDOM_VACATION_SWAP_RANGE = 15  # 15 days
# Variance for traffic type
RANDOM_TRAFFIC_TYPE_LOWER_BOUND = -2
RANDOM_TRAFFIC_TYPE_UPPER_BOUND = 2
RANDOM_TRAFFIC_TYPE_RANGE = NUM_ROWS_PER_DAY * 3  # 48 rows per 3 days
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
MODEL_BASE_DIR = '../classifier_models/'
MODEL_PERFORMANCE_FILE = '../classifier_models/ml_performance.json'
MODEL_PARSED_VALUES_FILE = '../output/parsed_values_dict.json'
DEFAULT_NUM_MODELS = 1
MODEL_NUM_FOLDS = 2

# Prediction columns schema
COLUMNS_PREDICTOR = ['hour', 'day', 'date_day', 'date_month', 'date_year']
