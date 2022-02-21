# Net constants
MIN_ROWS = 3
MIN_COLS = 3
MIN_LANES = 1
DISTANCE = 500
JUNCTION_TYPE = "traffic_light"
TL_TYPE = "static"
TL_LAYOUT = "opposites"


# File path constants
DEFAULT_DIR = "../output/"
DEFAULT_NODES_DIR = DEFAULT_DIR + "generated.nod.xml"
DEFAULT_EDGES_DIR = DEFAULT_DIR + "generated.edg.xml"
DEFAULT_NET_DIR = DEFAULT_DIR + "generated.net.xml"

# Info schemas
EDGE_SCHEMA = '  <edge id="{id}" from="{from_node}" to="{to_node}" priority="{priority}" numLanes="{num_lanes}"/> \n'
NODE_SCHEMA = '  <node id="{id}" x="{x}" y="{y}" type="{type}" tlType="{tl_type}" tlLayout="{tl_layout}"/> \n'
