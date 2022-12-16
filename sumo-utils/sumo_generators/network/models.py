from neomodel import StructuredNode, StringProperty, StructuredRel, IntegerProperty, RelationshipTo, \
    FloatProperty
from neomodel.contrib.spatial_properties import PointProperty


# RELATIONS
class AdjacentTLRelation(StructuredRel):
    """
    Relationship between two Traffic Lights nodes representing its adjacency
    """
    # Number of outbound/inbound roads
    num_out_edges = IntegerProperty(default=-1)
    num_in_edges = IntegerProperty(default=-1)
    # Summary of distances of all in-between connected roads
    distance = FloatProperty(default=-1.0)
    # Slope (total up and down) in path -> Not just a summary
    slope = FloatProperty(default=0.0)


class LaneRelation(StructuredRel):
    """
    Relationship between two Junction nodes representing the connecting road
    """
    # Name -> It should be Unique, but it is not supported yet on strings and relations
    name = StringProperty(required=True)
    # Distance between junctions = Road length
    distance = FloatProperty(default=-1.0)
    # Slope in degrees between junctions = Road slope degree
    slope = FloatProperty(default=0.0)
    # Maximum speed allowed
    max_speed = FloatProperty(default=50.0)
    # Average lane occupancy -> Only if there is a sensor associated to next junction
    avg_lane_occupancy = FloatProperty(default=0.0)
    # Average emission properties: CO2, CO, HCE, PMx, NOx, Noise
    avg_CO2_emission = FloatProperty(default=-1.0)
    avg_CO_emission = FloatProperty(default=-1.0)
    avg_HC_emission = FloatProperty(default=-1.0)
    avg_PMx_emission = FloatProperty(default=-1.0)
    avg_NOx_emission = FloatProperty(default=-1.0)
    avg_noise_emission = FloatProperty(default=-1.0)


class SensorToJunctionRelation(StructuredRel):
    """
    Relationship between a Sensor node and a Junction node representing the lane belonging of the sensor
    """
    # Position between junctions -> Relative to the lane
    pos = FloatProperty(default=-1.0)
    # Store the lane name
    lane = StringProperty(required=True)


# NODES
class Junction(StructuredNode):
    """
    Junction node representation
    """
    # Name
    name = StringProperty(unique_index=True, required=True)
    # Coordinate points
    # Cartesian -> X and Y -> Relative to axis
    cartesian_point = PointProperty(crs='cartesian')
    # Geospatial -> Latitude and Longitude -> Relative to world coordinates
    geospatial_point = PointProperty(crs='wgs-84')
    # Relation to another Junction using the LaneRelation relationship
    lane_to = RelationshipTo('Junction', "LANE_TO", model=LaneRelation)


class TrafficLight(Junction):
    """
    Traffic Light node representation that inherits from Junction node
    """
    # Actual TL program
    actual_program = StringProperty(default='')
    # Relation to an adjacent TrafficLight using the AdjacentTLRelation relationship
    adjacent_to = RelationshipTo('TrafficLight', "ADJACENT_TO", model=AdjacentTLRelation)


# There could be several detectors:
# Store geolocation with a radius action (e.g. zenith cameras)
# Type of sensor by its action area -> Single point (Passing detector), Rectangular (camera),
# Circular (environmental sensor or zenith camera)

class E1Detector(StructuredNode):
    """
    E1 detector node representing a passing detector
    """
    # Detector name
    name = StringProperty(unique_index=True, required=True)
    # Output related file -> Default to NUL as it will not be used
    file = StringProperty(default='NUL')
    # Information retrieval frequency
    freq = FloatProperty(default=1.0)
    # Relation to a specific Junction using the SensorToJunctionRelation
    to_junction = RelationshipTo('Junction', "TO_JUNCTION", model=SensorToJunctionRelation)
