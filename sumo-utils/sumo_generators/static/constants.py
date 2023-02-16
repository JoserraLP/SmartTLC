# Net constants
MIN_ROWS = 1
MIN_COLS = 1
MIN_LANES = 1
DISTANCE = 500
JUNCTION_TYPE = "traffic_light"
TL_TYPE = "static"
TL_LAYOUT = "opposites"
DEFAULT_TIME_PATTERN_FILE = '../time_patterns/generated_calendar.csv'

# File path constants
DEFAULT_DIR = "../config/"
# Define file names
DET_FILENAME = './out.xml'
DEFAULT_NODES_FILENAME = "topology.nod.xml"
DEFAULT_EDGES_FILENAME = "topology.edg.xml"
DEFAULT_NET_FILENAME = "topology.net.xml"
DEFAULT_DET_FILENAME = "topology.det.xml"
DEFAULT_TLL_FILENAME = "topology.tll.xml"
DEFAULT_ROUTE_FILENAME = "flows.rou.xml"
DEFAULT_CONFIG_FILENAME = "simulation.sumocfg"

# Define files paths
DET_FILE = DEFAULT_DIR + DET_FILENAME
DEFAULT_NODES_DIR = DEFAULT_DIR + DEFAULT_NODES_FILENAME
DEFAULT_EDGES_DIR = DEFAULT_DIR + DEFAULT_EDGES_FILENAME
DEFAULT_NET_DIR = DEFAULT_DIR + DEFAULT_NET_FILENAME
DEFAULT_DET_DIR = DEFAULT_DIR + DEFAULT_DET_FILENAME
DEFAULT_TLL_DIR = DEFAULT_DIR + DEFAULT_TLL_FILENAME
DEFAULT_ROUTE_DIR = DEFAULT_DIR + DEFAULT_ROUTE_FILENAME
DEFAULT_CONFIG_DIR = DEFAULT_DIR + DEFAULT_CONFIG_FILENAME

# Default date values
DEFAULT_DAY = "monday"
DEFAULT_DATE_DAY = "02"
DEFAULT_DATE_MONTH = "02"  # February
DEFAULT_DATE_YEAR = "2021"

# Date pattern fields
DATE_FIELDS = ['hour', 'day', 'date_day', 'date_month', 'date_year']

# Info schemas
EDGE_SCHEMA = '  <edge id="{id}" from="{from_node}" to="{to_node}" priority="{priority}" numLanes="{num_lanes}"/> \n'
NODE_SCHEMA = '  <node id="{id}" x="{x}" y="{y}" type="{type}" tlType="{tl_type}" tlLayout="{tl_layout}"/> \n'

# Flows generation
TIMESTEPS_PER_HOUR = 3600  # One hour is 3600 seconds

# Flows variables and its values
FLOWS_VALUES = {
    'very_low': {
        'vehs_lower_limit': 0,
        'vehsPerHour': 38,
        'vehs_upper_limit': 75
    },
    'low': {
        'vehs_lower_limit': 76,
        'vehsPerHour': 113,
        'vehs_upper_limit': 150
    },
    'med': {
        'vehs_lower_limit': 151,
        'vehsPerHour': 201,
        'vehs_upper_limit': 250
    },
    'high': {
        'vehs_lower_limit': 251,
        'vehsPerHour': 351,
        'vehs_upper_limit': 450
    },
    'very_high': {
        'vehs_lower_limit': 451,
        'vehsPerHour': 726,
        'vehs_upper_limit': 9999
    }
}

# Available traffic types
TRAFFIC_TYPES = {
    'very_low': 0,
    'low': 1,
    'med': 2,
    'high': 3,
    'very_high': 4
}

# Number of traffic types
NUM_TRAFFIC_TYPES = len(TRAFFIC_TYPES)

# MQTT constants
MQTT_URL = '172.20.0.2'
MQTT_PORT = 1883
TRAFFIC_INFO_TOPIC = 'traffic_info'
TRAFFIC_PREDICTION_TOPIC = 'traffic_prediction'
TURN_PREDICTION_TOPIC = 'turn_prediction'
TRAFFIC_ANALYSIS_TOPIC = 'traffic_analysis'
DEFAULT_QOS = 0

# Topology database constants
DB_IP_ADDRESS = '172.20.0.9:7687'
DB_USER = 'neo4j'
DB_PASSWORD = 'admin'

# Default detector file
DEFAULT_DETECTOR_FILE = 'detectors.add.xml'
DEFAULT_DETECTOR_POS = 10.0
DEFAULT_DETECTOR_FREQ = 1800

# Monitoring temporal window in number of TL cycles
DEFAULT_TEMPORAL_WINDOW = 5
# Define traffic light cycle length
POSSIBLE_CYCLES = {'urban': 90, 'non-urban': 120}

# Default list of topics
DEFAULT_TOPICS = ['#']

# Default turn dictionary
DEFAULT_TURN_DICT = {'turn_prob_right': 0.20, 'turn_prob_left': 0.20, 'turn_prob_forward': 0.60}
