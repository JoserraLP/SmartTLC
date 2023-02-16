import numpy as np
import pandas as pd
import traci
from neomodel import db, clear_neo4j_database, config
from neomodel.contrib.spatial_properties import NeomodelPoint
from traci._trafficlight import Logic

from sumo_generators.network.models import TrafficLight, Junction, LaneRelation, AdjacentTLRelation, E1Detector, \
    SensorToJunctionRelation


def create_outer_junction_info(info: list) -> dict:
    """
    Create an outer junction info dict

    :param info: junction information
    :type info: list
    :return: outer junction info and its edges
    :rtype: dict
    """
    outer_junction_info = {'from': info[0], 'to': info[1]}
    if len(info) == 4:
        # On both edges, remove the lane id "_X"
        outer_junction_info['from_edge'] = '_'.join(info[2].split('_')[:-1])
        outer_junction_info['to_edge'] = '_'.join(info[3].split('_')[:-1])

    return outer_junction_info


class NetworkTopology:
    """
    Network Topology class connection to Neo4J database

    :param ip_address: database IP address
    :type ip_address: str
    :param user: database user
    :type user: str
    :param password: database user password
    :type password: str
    :param traci: TraCI instance
    """

    def __init__(self, ip_address: str, user: str, password: str, traci):
        # Configure Neomodel database connection
        config.DATABASE_URL = f'bolt://{user}:{password}@{ip_address}'
        # Store the database
        self._db = db
        # Store traci instance
        self._traci = traci

    def close(self) -> None:
        """
        Close connection to database

        :return: None
        """
        self._db.driver.close()

    def clear_database(self) -> None:
        """
        Clear database information

        :return: None
        """
        clear_neo4j_database(self._db)

    def load_data(self, edges_df: pd.DataFrame, junctions_df: pd.DataFrame) -> None:
        """
        Load all topology data and its relations into the database

        :param edges_df: edges dataframe
        :type edges_df: Pandas DataFrame
        :param junctions_df: junctions dataframe
        :type junctions_df: Pandas Dataframe
        :return: None
        """

        # First create the junctions
        for index, junction in junctions_df.iterrows():
            self.create_junction(junction)

        # Second create the edge connections
        for index, edge in edges_df.iterrows():
            self.create_edge(edge)

        # Thirdly create the adjacent traffic lights connections
        self.create_adjacent_tl_relation()

    # CREATE METHODS
    @staticmethod
    def create_junction(junction: pd.Series) -> None:
        """
        Create a junction and insert it into the database

        :param junction: junction information
        :type junction: pandas Series
        :return: None
        """
        # Store junction name
        name = junction['node_id']
        # Store cartesian coordinates
        cartesian_point_x, cartesian_point_y = junction['node_x'], junction['node_y']

        # Store the latitude and longitude if available
        if 'node_lon' in junction or 'node_lat' in junction:
            geospatial_point_lon = junction['node_lon'] if not np.isnan(junction['node_lon']) else -1.0
            geospatial_point_lat = junction['node_lat'] if not np.isnan(junction['node_lat']) else -1.0
        else:
            geospatial_point_lon, geospatial_point_lat = -1.0, -1.0

        # Create traffic light if its type
        if 'traffic_light' in junction['node_type']:
            traffic_light_name = name
            # Get actual traffic light program
            actual_program = str(traci.trafficlight.getAllProgramLogics(traffic_light_name))

            # Create a Traffic Light with same info
            TrafficLight(name=name, cartesian_point=NeomodelPoint(x=cartesian_point_x, y=cartesian_point_y,
                                                                  crs='cartesian'),
                         geospatial_point=NeomodelPoint(latitude=geospatial_point_lat,
                                                          longitude=geospatial_point_lon,
                                                          crs='wgs-84'), actual_program=actual_program,
                         junction_type=junction['node_type']).save()
        else:

            # Create junction type based on it is outer fringe (dead end) or other type
            junction_type = 'dead_end' if 'node_fringe' in junction and junction['node_fringe'] == 'outer' \
                else junction['node_type']

            # Create junction
            Junction(name=name, cartesian_point=NeomodelPoint(x=cartesian_point_x, y=cartesian_point_y,
                                                              crs='cartesian'),
                     geospatial_point=NeomodelPoint(latitude=geospatial_point_lat,
                                                      longitude=geospatial_point_lon,
                                                      crs='wgs-84'), junction_type=junction_type).save()

    def create_edge(self, edge: pd.Series) -> None:
        """
        Create the "lane_to" relations of a given edge in the network

        :param edge: edge information
        :type edge: pandas Series
        :return: None
        """

        # Iterate over the lanes of an edge
        for lane in range(0, int(edge['edge_numLanes'])):
            # Retrieve lane id
            lane_id = str(edge['edge_id']) + '_' + str(lane)

            # Retrieve source and destination target
            source = Junction.nodes.get(name=edge['edge_from'])
            target = Junction.nodes.get(name=edge['edge_to'])

            # Create the LaneRelation using its dict representation
            source.lane_to.connect(target,
                                   LaneRelation(name=lane_id, max_speed=str(self._traci.lane.getMaxSpeed(lane_id)),
                                                distance=str(self._traci.lane.getLength(lane_id))).__dict__).save()

    def create_adjacent_tl_relation(self):
        """
        Create the "adjacent_to" relation of all the traffic lights of the network

        :return: None
        """

        # Get all traffic lights nodes' name
        traffic_lights = [traffic_light.name for traffic_light in TrafficLight.nodes.all()]

        # Iterate over the traffic lights to generate adjacency
        for source_tl in traffic_lights:
            for target_tl in traffic_lights:
                # If source and destination are not the same
                if source_tl != target_tl:
                    # Create the shortest path between two traffic lights query
                    # Limited to 100 as it is required to define and upper limit
                    query = "MATCH p = shortestPath((n:TrafficLight {name: '" + source_tl + \
                            "'})-[:LANE_TO*..100]->(m:TrafficLight {name: '" + target_tl \
                            + "'})) RETURN nodes(p) as nodes"

                    # Perform the query
                    results, _ = self._db.cypher_query(query)

                    # Retrieve the junction names of the path between two traffic lights.
                    # Iterating over the list of results and getting each possible value
                    path = [Junction.inflate(node).name for result in [result[0] for result in results] for node in
                            result]

                    # If there exists a path between the traffic lights
                    if path:
                        # Remove first and last items from the connected nodes as they are source and target
                        inner_nodes = path[1:-1]

                        # If there are not any traffic lights on the inner path, both traffic lights are adjacent
                        if not any(inner_node in traffic_lights for inner_node in inner_nodes):
                            # Retrieve source and destination nodes
                            source_node = Junction.nodes.get(name=source_tl)
                            target_node = Junction.nodes.get(name=target_tl)

                            # Create the relation between adjacent traffic lights -> Store the dict representation
                            # of the object
                            source_node.adjacent_to.connect(target_node, AdjacentTLRelation().__dict__).save()

    def create_detector_node_relation(self, detector_info: dict) -> None:
        """
        Create detector and node relation

        :param detector_info: detector information
        :type detector_info: dict
        :return: None
        """
        # Create detector
        detector = E1Detector(name=detector_info['id'], file=detector_info['file'], freq=detector_info['freq']).save()

        # Create relation
        sensor_relation = SensorToJunctionRelation(pos=detector_info['pos'], lane=detector_info['lane'])

        # Get the junction where the lane is connected
        results, _ = self._db.cypher_query("MATCH (n:Junction)-[r:LANE_TO {name:'" + detector_info['lane'] +
                                           "'}]->(m:Junction) RETURN m.name;")

        # Get next junction as it should exist always
        junction = Junction.nodes.get(name=results[0][0])

        # Create relation from the detector to the junction
        detector.to_junction.connect(junction, sensor_relation.__dict__).save()

    # GET METHODS
    @staticmethod
    def get_all_adjacent_tl_ids() -> dict:
        """
        Get all adjacent traffic lights per each traffic light

        :return: adjacent traffic lights id
        :rtype: list
        """
        # Create empty dict
        adjacent_tls_per_tl = {}

        # Iterate over all traffic lights
        for traffic_light in TrafficLight.nodes.all():
            # Retrieve the traffic lights' name of the "adjacent_to" relation and store into the dict
            adjacent_tls_per_tl[traffic_light.name] = [adjacent_tl.name for adjacent_tl in
                                                       traffic_light.adjacent_to.all()]

        return adjacent_tls_per_tl

    @staticmethod
    def get_adjacent_tls(tl_name: str) -> list:
        """
        Get adjacent traffic lights from a given traffic light

        :param tl_name: traffic light name
        :type tl_name: str
        :return: adjacent traffic lights id
        :rtype: list
        """
        # Get Traffic Light node and its "adjacent_to" relations
        return [adjacent_tl for adjacent_tl in TrafficLight.nodes.get(name=tl_name).adjacent_to.all()]

    def get_junction_detectors(self, junction_name: str) -> list:
        """
        Get detectors related to a given junction

        :param junction_name: junction name
        :type junction_name: str
        :return: detector names
        :rtype: list
        """
        # Create the query
        query = "MATCH (n:E1Detector)-[r:TO_JUNCTION]->(m {name: '" + junction_name + "'}) RETURN n;"
        # Perform query
        results, _ = self._db.cypher_query(query)
        # Process results and return a list with the names
        return [E1Detector.inflate(detector[0]).name for detector in results]

    @staticmethod
    def get_tl_names() -> list:
        """
        Get all the traffic lights names

        :return: list with all traffic lights
        :rtype: list
        """
        return [traffic_light.name for traffic_light in TrafficLight.nodes.all()]

    @staticmethod
    def get_tl_roads(tl_name: str) -> list:
        """
        Get outbound and inbound traffic lights connected roads from a given traffic light

        :param tl_name: traffic light name
        :type tl_name: str
        :return: outbound and inbound connected roads
        :rtype: list
        """
        # Get all roads
        query = "MATCH (n:TrafficLight {name:'" + tl_name + "'})-[r:LANE_TO]-(m:Junction) RETURN r;"

        # Perform the query
        results, meta = db.cypher_query(query)

        # Get all roads
        all_roads = [LaneRelation.inflate(rel) for result in [item for item in results] for rel in result]

        # Create outbound and inbound lists
        outbound_roads, inbound_roads = [], []

        # Get Traffic Light DB id
        tl_id = TrafficLight.nodes.get(name=tl_name).id

        # Iterate over roads
        for road in all_roads:
            # outbound road
            if road.start_node().id == tl_id:
                outbound_roads.append(road)
            # inbound road
            elif road.end_node().id == tl_id:
                inbound_roads.append(road)

        # Return roads as list
        return [outbound_roads, inbound_roads]

    @staticmethod
    def get_outer_junctions(bound: str, edges: bool = False) -> list:
        """
        Get outer outbound and inbound junctions

        :param bound: type of bound. It can be 'inbound' or 'outbound'
        :type bound: str
        :param edges: flag to return related edges
        :type edges: bool
        :return: outer junctions
        :rtype: list
        """
        if bound not in ['inbound', 'outbound']:
            raise Exception("Bound parameter is not valid. It should be 'inbound' or 'outbound'")

        # Retrieve type of bound and create the relation query
        relation_query = "<-[r:LANE_TO]-" if bound == 'outbound' else "-[r:LANE_TO]->"
        # Add edge fields to query
        edges_query = "-[s:LANE_TO]->(:Junction)" if edges else ""
        add_edges_info = ",r.name,s.name" if edges else ""

        # Get all outer junctions
        query = f"MATCH (n:Junction){relation_query}(m:Junction){edges_query} WHERE n.junction_type = 'dead_end' " \
                f"RETURN DISTINCT n.name, m.name{add_edges_info};"

        # Perform the query
        results, meta = db.cypher_query(query)

        # Get all inbound outer junctions
        outer_junctions = [create_outer_junction_info(result) for result in [item for item in results]]

        # Remove duplicate values and reset index
        outer_junctions_pd = pd.DataFrame(outer_junctions).drop_duplicates().reset_index(drop=True)

        return outer_junctions_pd.to_dict(orient='records')

    # UPDATE METHODS
    def update_lanes_info(self, tl_id: str, contextual_lane_info: dict):
        """
        Update data related to the lanes connected to a traffic light
        """

        # Create the query for retrieving the lanes
        query = "MATCH (n: TrafficLight {name: '" + tl_id + "'})<-[r:LANE_TO]-(m) RETURN r;"

        # Perform query
        results, _ = self._db.cypher_query(query)

        # Process the result
        lanes = [LaneRelation.inflate(lane[0]) for lane in results]

        # Iterate over the contextual_lane_info -> Until last item as it is related to the TL itself
        for lane_info in contextual_lane_info[:-1]:
            # Get lane info and store the values
            lane = [lane for lane in lanes if lane.name == lane_info['lane']][0]

            # Store properties
            lane.avg_lane_occupancy = round(lane_info['avg_lane_occupancy'], 2)
            lane.avg_CO2_emission = lane_info['avg_CO2_emission']
            lane.avg_CO_emission = lane_info['avg_CO_emission']
            lane.avg_HC_emission = lane_info['avg_HC_emission']
            lane.avg_PMx_emission = lane_info['avg_PMx_emission']
            lane.avg_NOx_emission = lane_info['avg_NOx_emission']
            lane.avg_noise_emission = lane_info['avg_noise_emission']
            # Save the data
            lane.save()

    def update_traffic_light_program(self, tl_id: str, tl_program: Logic):
        # Create the query for retrieving the traffic light
        query = "MATCH (n: TrafficLight {name: '" + tl_id + "'}) RETURN n;"

        # Perform query
        results, _ = self._db.cypher_query(query)

        # Process the result
        tl = [TrafficLight.inflate(traffic_light[0]) for traffic_light in results][0]

        # Update the traffic light actual program
        tl.actual_program = str(tl_program)
        # Save the tl info
        tl.save()
