# Net constants
MIN_ROWS = 3
MIN_COLS = 3
MIN_LANES = 1
DISTANCE = 500
DET_DISTANCE = 25
DET_FREQ = 1800
JUNCTION_TYPE = "traffic_light"
TL_TYPE = "static"
TL_LAYOUT = "opposites"
DEFAULT_TIME_PATTERN_FILE = '../time_patterns/generated_calendar.csv'

# Traffic proportions
TRAFFIC_PROPORTIONS = [0.25, 0.50, 1, 2, 4]

# Bounds on phase time
LOWER_BOUND_TIME_PHASE = 20
UPPER_BOUND_TIME_PHASE = 70
MAXIMUM_TIME_PHASE = 80
MAXIMUM_TIME_BOUND_PHASE = UPPER_BOUND_TIME_PHASE - LOWER_BOUND_TIME_PHASE


# File path constants
DEFAULT_DIR = "../output/"
DET_FILE = DEFAULT_DIR + './out.xml'
DEFAULT_NODES_DIR = DEFAULT_DIR + "topology.nod.xml"
DEFAULT_EDGES_DIR = DEFAULT_DIR + "topology.edg.xml"
DEFAULT_NET_DIR = DEFAULT_DIR + "topology.net.xml"
DEFAULT_DET_DIR = DEFAULT_DIR + "topology.det.xml"
DEFAULT_TLL_DIR = DEFAULT_DIR + "topology.tll.xml"
DEFAULT_ROUTE_DIR = DEFAULT_DIR + "flows.rou.xml"
DEFAULT_CONFIG_DIR = DEFAULT_DIR + "simulation.sumocfg"

# Info schemas
EDGE_SCHEMA = '  <edge id="{id}" from="{from_node}" to="{to_node}" priority="{priority}" numLanes="{num_lanes}"/> \n'
NODE_SCHEMA = '  <node id="{id}" x="{x}" y="{y}" type="{type}" tlType="{tl_type}" tlLayout="{tl_layout}"/> \n'

# Flows generation
TIMESTEPS_PER_HALF_HOUR = 1800  # Half hour is 1800 seconds

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

# Traffic type relation
TRAFFIC_TYPE_RELATION = {
    # (NS, EW)
    0: ('very_low', 'very_low'),
    1: ('very_low', 'low'),
    2: ('low', 'very_low'),
    3: ('low', 'low'),
    4: ('low', 'med'),
    5: ('low', 'high'),
    6: ('med', 'low'),
    7: ('med', 'med'),
    8: ('med', 'high'),
    9: ('high', 'low'),
    10: ('high', 'med'),
    11: ('high', 'high'),
}

TRAFFIC_TYPES = {
    'very_low': 0,
    'low': 1,
    'med': 2,
    'high': 3
}
