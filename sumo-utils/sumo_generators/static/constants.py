# Net constants
MIN_ROWS = 3
MIN_COLS = 3
MIN_LANES = 1
DISTANCE = 500
DET_DISTANCE = 25
DET_FREQ = 1800
DET_FILE = '../out.xml'
JUNCTION_TYPE = "traffic_light"
TL_TYPE = "static"
TL_LAYOUT = "opposites"

# Traffic proportions
TRAFFIC_PROPORTIONS = [0.25, 0.50, 1, 2, 4]

# Bounds on phase time
LOWER_BOUND_TIME_PHASE = 20
UPPER_BOUND_TIME_PHASE = 70
MAXIMUM_TIME_PHASE = 80
MAXIMUM_TIME_BOUND_PHASE = UPPER_BOUND_TIME_PHASE - LOWER_BOUND_TIME_PHASE


# File path constants
DEFAULT_DIR = "../output/"
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
