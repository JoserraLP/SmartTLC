import ast
import math

import paho.mqtt.client as mqtt
from tl_controller.static.constants import TRAFFIC_TYPE_TL_ALGORITHMS, ERROR_THRESHOLD, MQTT_URL, MQTT_PORT, \
    TRAFFIC_PREDICTION_TOPIC, TURN_PREDICTION_TOPIC, ANALYSIS_TOPIC, NUM_TRAFFIC_TYPES


def retrieve_junction_turns_ids(roads, rows, cols):
    junction_turns = {}

    for road in roads:
        # Retrieve source and destination nodes and its ids
        source, destination = road.split('_')
        source_id, destination_id = int(source[1:]), int(destination[1:])

        next_forward_junction, next_right_junction, next_left_junction, orientation = '', '', '', ''

        if 'n' in source:
            orientation = 'ns'
            next_forward_junction = f'c{destination_id + cols}'
            if destination_id % cols == 1:  # Left nodes
                next_left_junction = f'c{destination_id + 1}'
            elif destination_id % cols == 0:  # Right nodes
                next_right_junction = f'c{destination_id - 1}'
            else:  # Center nodes
                next_right_junction = f'c{destination_id - 1}'
                next_left_junction = f'c{destination_id + 1}'
        elif 's' in source:
            orientation = 'ns'
            next_forward_junction = f'c{destination_id - cols}'
            if destination_id % cols == 1:  # Left nodes
                next_right_junction = f'c{destination_id + 1}'
            elif destination_id % cols == 0:  # Right nodes
                next_left_junction = f'c{destination_id - 1}'
            else:  # Center nodes
                next_left_junction = f'c{destination_id - 1}'
                next_right_junction = f'c{destination_id + 1}'
        elif 'e' in source:
            orientation = 'ew'
            next_forward_junction = f'c{destination_id - 1}'
            if math.ceil(destination_id / cols) == 1:  # Lower nodes
                next_left_junction = f'c{destination_id + cols}'
            elif math.ceil(destination_id / cols) == rows:  # Upper nodes
                next_right_junction = f'c{destination_id - cols}'
            else:  # Center nodes
                next_right_junction = f'c{destination_id - cols}'
                next_left_junction = f'c{destination_id + cols}'
        elif 'w' in source:
            orientation = 'ew'
            next_forward_junction = f'c{destination_id + 1}'
            if math.ceil(destination_id / cols) == 1:  # Lower nodes
                next_right_junction = f'c{destination_id + cols}'
            elif math.ceil(destination_id / cols) == rows:  # Upper nodes
                next_left_junction = f'c{destination_id - cols}'
            else:  # Center nodes
                next_right_junction = f'c{destination_id + cols}'
                next_left_junction = f'c{destination_id - cols}'
        else:  # center nodes
            if source_id == destination_id - cols:  # Going down
                orientation = 'ns'
                if destination_id % cols == 1:  # Left nodes
                    next_left_junction = f'c{destination_id + 1}'
                elif destination_id % cols == 0:  # Right nodes
                    next_right_junction = f'c{destination_id - 1}'
                else:  # Center nodes
                    next_right_junction = f'c{destination_id - 1}'
                    next_left_junction = f'c{destination_id + 1}'
                if math.ceil(destination_id / cols) != rows:  # Upper nodes
                    next_forward_junction = f'c{destination_id + cols}'
            elif source_id == destination_id + cols:  # Going up
                orientation = 'ns'
                if destination_id % cols == 1:  # Left nodes
                    next_right_junction = f'c{destination_id + 1}'
                elif destination_id % cols == 0:  # Right nodes
                    next_left_junction = f'c{destination_id - 1}'
                else:  # Center nodes
                    next_left_junction = f'c{destination_id - 1}'
                    next_right_junction = f'c{destination_id + 1}'
                if math.ceil(destination_id / cols) != 1:  # Not lower nodes
                    next_forward_junction = f'c{destination_id - cols}'
            elif source_id == destination_id + 1:  # Going right
                orientation = 'ew'
                if math.ceil(destination_id / cols) == 1:  # Lower nodes
                    next_left_junction = f'c{destination_id + cols}'
                elif math.ceil(destination_id / cols) == rows:  # Upper nodes
                    next_right_junction = f'c{destination_id - cols}'
                else:  # Center nodes
                    next_right_junction = f'c{destination_id - cols}'
                    next_left_junction = f'c{destination_id + cols}'
                if destination_id % cols != 1:  # Not left nodes
                    next_forward_junction = f'c{destination_id - 1}'
            elif source_id == destination_id - 1:  # Going left
                orientation = 'ew'
                if math.ceil(destination_id / cols) == 1:  # Lower nodes
                    next_right_junction = f'c{destination_id + cols}'
                elif math.ceil(destination_id / cols) == rows:  # Upper nodes
                    next_left_junction = f'c{destination_id - cols}'
                else:  # Center nodes
                    next_right_junction = f'c{destination_id + cols}'
                    next_left_junction = f'c{destination_id - cols}'
                if destination_id % cols != 0:  # Not right nodes
                    next_forward_junction = f'c{destination_id + 1}'

        junction_turns[road] = {'right': {'junction': next_right_junction, 'prob': 0.0},
                                'left': {'junction': next_left_junction, 'prob': 0.0},
                                'forward': {'junction': next_forward_junction, 'prob': 0.0},
                                'orientation': orientation}
    return junction_turns


class TrafficLightAdapter:
    """
    Traffic Light Adapter class
    """

    def __init__(self, traffic_prediction=None, traffic_analysis=None, turn_prediction=None, roads=None,
                 mqtt_url: str = MQTT_URL,
                 mqtt_port: int = MQTT_PORT, rows: int = -1, cols: int = -1, num_adapt_items: int = 0):
        """
        TraCISimulator initializer.

        :param traffic_prediction: traffic prediction dict. Default is None.
        :type traffic_prediction: dict
        :param traffic_analysis: traffic analysis dict. Default is None.
        :type traffic_analysis: dict
        :param turn_prediction: turn prediction dict. Default is None.
        :type turn_prediction: dict
        :param roads: Roads list. Default is None.
        :type roads: list
        :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
        :type mqtt_url: str
        :param mqtt_port: MQTT middleware broker port. Default to 1883.
        :type mqtt_port: int
        :param num_adapt_items: number of items for real-time/historic information relevance adaptation. Default to 0.
        :type num_adapt_items: int
        :param rows: topology rows. Default to -1.
        :type rows: int
        :param cols: topology cols. Default to -1.
        :type cols: int
        """
        # Store traffic prediction, traffic analysis and turn prediction
        self._traffic_prediction = traffic_prediction
        self._traffic_analysis = traffic_analysis
        self._turn_prediction = turn_prediction

        # Define topology rows and cols
        self._rows = rows
        self._cols = cols

        # Define junction connections
        self._junctions_per_road = retrieve_junction_turns_ids(roads, rows, cols)

        # Create the MQTT client, its callbacks and its connection to the broker
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self.on_connect
        self._mqtt_client.on_message = self.on_message
        self._mqtt_client.connect(mqtt_url, mqtt_port)
        self._mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback called when the client connects to the broker.

        :param client: MQTT client
        :param userdata: MQTT client data
        :param flags: MQTT connection flags
        :param rc: MQTT connection response code
        :return: None
        """
        if rc == 0:  # Connection established
            # Subscribe to the traffic prediction, analysis and turn prediction topics
            self._mqtt_client.subscribe(TRAFFIC_PREDICTION_TOPIC)
            self._mqtt_client.subscribe(ANALYSIS_TOPIC)
            self._mqtt_client.subscribe(TURN_PREDICTION_TOPIC)

    def on_message(self, client, userdata, msg):
        """
        Callback called when the client receives a message from to the broker.
        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        # Parse message to dict
        traffic_info = ast.literal_eval(msg.payload.decode('utf-8'))

        # Check the topic it comes from
        if msg.topic == TRAFFIC_PREDICTION_TOPIC:
            # Retrieve predicted traffic type
            self._traffic_prediction = traffic_info
        if msg.topic == ANALYSIS_TOPIC:
            # Retrieve analyzed traffic type
            self._traffic_analysis = traffic_info
        if msg.topic == TURN_PREDICTION_TOPIC:
            # Retrieve turn prediction
            self._turn_prediction = traffic_info

    def get_new_tl_program(self):
        """
        Retrieve the new traffic light program based on the analyzer, predictor or both.

        :return: new tl program per traffic light
        :rtype: dict
        """
        current_traffic_type = None

        # Store the turns probabilities per road
        if self._turn_prediction:
            for road, turns in self._turn_prediction.items():
                # Store the turn probabilities
                self._junctions_per_road[road]['right']['prob'] = turns[0]
                self._junctions_per_road[road]['left']['prob'] = turns[1]
                self._junctions_per_road[road]['forward']['prob'] = turns[2]

                print(f"Road {road} (with orientation {self._junctions_per_road[road]['orientation']}) "
                      f"has the following turn probabilities:"
                      f"\n Right {turns[0]} to junction {self._junctions_per_road[road]['right']['junction']}"
                      f"\n Left {turns[1]} to junction {self._junctions_per_road[road]['left']['junction']}"
                      f"\n Forward {turns[2]} to junction {self._junctions_per_road[road]['forward']['junction']}")

        # If only analyzer is deployed
        if self._traffic_analysis and not self._traffic_prediction:
            current_traffic_type = self._traffic_analysis
        # If only predictor is deployed
        elif self._traffic_prediction and not self._traffic_analysis:
            current_traffic_type = self._traffic_prediction
        elif self._traffic_analysis and self._traffic_prediction:
            current_traffic_type = dict()
            # If both analyzer and predictor are deployed
            if self._traffic_analysis and self._traffic_prediction:
                # It is chosen the traffic_analysis but can be used both as they have the same information
                for traffic_light in self._traffic_analysis.keys():
                    # update this
                    self.calculate_actual_traffic_type(current_traffic_type=current_traffic_type,
                                                       traffic_light=traffic_light)

                # Store the difference between prediction and analysis
                # self._adapt_items.append(abs(self._traffic_prediction - self._traffic_analysis))

                # Remove used traffic information -> To check again if there is information available
                self._traffic_analysis = None
                self._traffic_prediction = None
                self._turn_prediction = None

        adapter_tl_programs = dict()

        if current_traffic_type is not None:
            # If the traffic type exists get the new traffic light program per traffic light
            for traffic_light, traffic_type in current_traffic_type.items():
                adapter_tl_programs[traffic_light] = TRAFFIC_TYPE_TL_ALGORITHMS[str(int(traffic_type))]
        else:
            adapter_tl_programs = None

        return adapter_tl_programs

    def close_connection(self):
        """
        Close MQTT client connection
        """
        self._mqtt_client.loop_stop()

    def calculate_actual_traffic_type(self, current_traffic_type, traffic_light):
        # Calculate the difference between the traffic types
        error_distance = self._traffic_analysis[traffic_light] \
                         - self._traffic_prediction[traffic_light]
        # If the distance is less than the threshold
        if abs(error_distance) <= ERROR_THRESHOLD:
            # The analyzer is right, use its value
            current_traffic_type[traffic_light] = self._traffic_analysis[traffic_light]
        # Otherwise calculate the weighted value
        else:
            # 1/3 closest to the analyzer as it is in real time
            new_traffic_type = self._traffic_analysis[traffic_light] \
                               - int(error_distance / 3)
            if new_traffic_type >= 0 or new_traffic_type <= NUM_TRAFFIC_TYPES:
                # If calculated value is valid, store it
                current_traffic_type[traffic_light] = new_traffic_type

    '''
    def calculate_weighted_traffic_type(self, tl_id):
        # Retrieve traffic type from analyzer and predictor
        analysis_traffic_type = self._traffic_analysis[tl_id]
        predicted_traffic_type = self._traffic_prediction[tl_id]

        print("--------------------------------")
        print(f"Predicted traffic type: {int(predicted_traffic_type)}")
        print(f"Analysis traffic type: {analysis_traffic_type}")

        # Retrieve current traffic type values
        analysis_traffic_type_ns, analysis_traffic_type_ew = TRAFFIC_TYPE_RELATION[analysis_traffic_type]
        predicted_traffic_type_ns, predicted_traffic_type_ew = TRAFFIC_TYPE_RELATION[predicted_traffic_type]

        # Retrieve current traffic type values
        analysis_num_veh_ns, analysis_num_veh_ew = FLOWS_VALUES[analysis_traffic_type_ns]['vehsPerHour'], \
                                                   FLOWS_VALUES[analysis_traffic_type_ew]['vehsPerHour']

        predicted_num_veh_ns, predicted_num_veh_ew = FLOWS_VALUES[predicted_traffic_type_ns]['vehsPerHour'], \
                                                   FLOWS_VALUES[predicted_traffic_type_ew]['vehsPerHour']

        # Calculate weight per direction
        weight_ns = abs(predicted_num_veh_ns - analysis_num_veh_ns)/self._max_error_value
        weight_ew = abs(predicted_num_veh_ew - analysis_num_veh_ew)/self._max_error_value

        print(f"Weight NS: {weight_ns}")
        print(f"Weight EW: {weight_ew}")

        # Retrieve the actual traffic type
        traffic_type_ns = round((1 - weight_ns) * TRAFFIC_TYPES[predicted_traffic_type_ns] +
                                 weight_ns * TRAFFIC_TYPES[analysis_traffic_type_ns])

        traffic_type_ew = round((1 - weight_ew) * TRAFFIC_TYPES[predicted_traffic_type_ew] +
                                 weight_ew * TRAFFIC_TYPES[analysis_traffic_type_ew])

        print(f"Traffic type NS: {traffic_type_ns}")
        print(f"Traffic type EW: {traffic_type_ew}")

        # Get traffic type name by id
        ns_traffic_type_name = [k for k, v in TRAFFIC_TYPES.items() if v == traffic_type_ns][0]
        ew_traffic_type_name = [k for k, v in TRAFFIC_TYPES.items() if v == traffic_type_ew][0]

        actual_traffic_name = (ns_traffic_type_name, ew_traffic_type_name)

        actual_traffic_type = [k for k, v in TRAFFIC_TYPE_RELATION.items() if v == actual_traffic_name][0]

        print(f"Actual Traffic type: {actual_traffic_type}")

        return actual_traffic_type
    '''
