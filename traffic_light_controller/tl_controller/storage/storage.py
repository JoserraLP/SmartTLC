import copy


class TrafficLightInfoStorage:
    """
    Traffic Light Info Storage  class to gather all the traffic related information 
    """

    def __init__(self, roads: list, passing_veh_n_s: int = 0, passing_veh_e_w: int = 0,
                 waiting_time_veh_n_s: int = 0, waiting_time_veh_e_w: int = 0, turning_forward: int = 0,
                 turning_right: int = 0, turning_left: int = 0, actual_program: str = '') -> None:
        """
        TrafficInfoStorage initializer

        :param roads: roads names list
        :type roads: list
        :param passing_veh_n_s: number of passing vehicles on NS direction. Default to 0.
        :type passing_veh_n_s: int
        :param passing_veh_e_w: number of passing vehicles on EW direction. Default to 0.
        :type passing_veh_e_w: int
        :param waiting_time_veh_n_s: waiting time on NS direction. Default to 0.
        :type waiting_time_veh_n_s: int
        :param waiting_time_veh_e_w: waiting time on EW direction. Default to 0.
        :type waiting_time_veh_e_w: int
        :param turning_forward: number of vehicles going forward. Default to 0.
        :type turning_forward: int
        :param turning_right: number of vehicles turning right. Default to 0.
        :type turning_right: int
        :param turning_left: number of vehicles turning left. Default to 0.
        :type turning_left: int
        :param actual_program: actual traffic light program. Default to ''.
        :type actual_program: str
        :return: None
        """
        # Initialize variables
        # Passing vehicles on both directions
        self._passing_veh_n_s, self._passing_veh_e_w = passing_veh_n_s, passing_veh_e_w
        # Waiting time on both directions
        self._waiting_time_veh_n_s, self._waiting_time_veh_e_w = waiting_time_veh_n_s, waiting_time_veh_e_w
        # Vehicles passed on the traffic light
        self._vehicles_passed = set()
        # Turning vehicles
        self._turning_vehicles = {'forward': turning_forward, 'right': turning_right, 'left': turning_left,
                                  'vehicles_passed': set()}
        # Roads load by parameter
        self._roads = roads
        # Actual program
        self._actual_program = actual_program
        # Date info
        self._date_info = None

    def reset_traffic_info(self) -> None:
        """
        Restore to default values the traffic light information

        :return: None
        """
        # Passing vehicles on both directions
        self._passing_veh_n_s, self._passing_veh_e_w = 0, 0
        # Waiting time on both directions
        self._waiting_time_veh_n_s, self._waiting_time_veh_e_w = 0, 0
        # Turning vehicles
        self._turning_vehicles['forward'], self._turning_vehicles['right'], self._turning_vehicles['left'] = 0, 0, 0

    def increase_turning_vehicles(self, turn: str) -> None:
        """
        Increase the number of turning vehicles by 1 on the given turn

        :param turn: turn direction
        :type turn: str
        :return: None
        """
        self._turning_vehicles[turn] += 1

    def append_turning_vehicle(self, vehicle_id: str) -> None:
        """
        Append a vehicle to the list of turning vehicles of the traffic light

        :param vehicle_id: vehicle identifier
        :type vehicle_id: str
        :return: None
        """
        self._turning_vehicles['vehicles_passed'].add(vehicle_id)

    def is_vehicle_turning_counted(self, vehicle_id: str) -> bool:
        """
        Check if a turning vehicles has been counted previously

        :param vehicle_id: vehicle identifier
        :type vehicle_id: str
        :return: True if it is counted, False otherwise
        :rtype: bool
        """
        return vehicle_id in self._turning_vehicles['vehicles_passed']

    """ UTILS """

    def get_processed_publish_info(self) -> dict:
        """
        Get the info that will be published with a valid format

        :return: valid publish info
        :rtype: dict
        """
        return dict(**dict(self.get_publish_info()), **dict(self._date_info))

    """ EXTERNAL TRAFFIC COMPONENTS UTILS """

    def get_publish_info(self) -> dict:
        """
        Process the traffic_info and date_info dictionaries to be formatted to a valid Telegraf schema

        :return: dict with passing vehicles on NS and EW direction
        :rtype: dict
        """
        traffic_info_dict = {'passing_veh_n_s': self._passing_veh_n_s,
                             'passing_veh_e_w': self._passing_veh_e_w,
                             'waiting_time_veh_n_s': self._waiting_time_veh_n_s,
                             'waiting_time_veh_e_w': self._waiting_time_veh_e_w,
                             'turning_vehicles': copy.deepcopy(self._turning_vehicles),
                             'roads': self._roads,
                             'actual_program': self._actual_program
                             }

        # Remove the turning vehicles set
        traffic_info_dict['turning_vehicles'].pop("vehicles_passed", None)

        return traffic_info_dict

    def get_traffic_analyzer_info(self) -> dict:
        """
        Get the traffic analyzer required information (only passing vehicles per direction)

        :return: dict with passing vehicles on NS and EW direction
        :rtype: dict
        """
        return {'passing_veh_n_s': self._passing_veh_n_s, 'passing_veh_e_w': self._passing_veh_e_w}

    def get_traffic_predictor_info(self, date: bool = True) -> None:
        pass

    def get_turn_predictor_info(self) -> None:
        pass

    """ CLASS ATTRIBUTES UTILS """

    def increase_passing_vehicles_n_s(self, num_veh_n_s: int) -> None:
        """
        Increase the number of passing vehicles on the NS direction

        :param num_veh_n_s: number of vehicles on the NS direction
        :type num_veh_n_s: int
        :return: None
        """
        self._passing_veh_n_s += num_veh_n_s

    def increase_passing_vehicles_e_w(self, num_veh_e_w: int) -> None:
        """
        Increase the number of passing vehicles on the EW direction

        :param num_veh_e_w: number of vehicles on the EW direction
        :type num_veh_e_w: int
        :return: None
        """
        self._passing_veh_e_w += num_veh_e_w

    def increase_waiting_time_n_s(self, waiting_time_n_s: float) -> None:
        """
        Increase the waiting time on the NS direction

        :param waiting_time_n_s: waiting time on the NS direction
        :type waiting_time_n_s: float
        :return: None
        """
        self._waiting_time_veh_n_s += waiting_time_n_s

    def increase_waiting_time_e_w(self, waiting_time_e_w: float) -> None:
        """
        Increase the waiting time on the EW direction

        :param waiting_time_e_w: waiting time on the EW direction
        :type waiting_time_e_w: float
        :return: None
        """
        self._waiting_time_veh_e_w += waiting_time_e_w

    def update_passing_vehicles(self, passing_veh: set) -> None:
        """
        Append new passing vehicles

        :param passing_veh: new passing vehicles
        :type passing_veh: set
        :return: None
        """
        self._vehicles_passed.update(passing_veh)

    def remove_passed_vehicles(self, vehicles: set) -> None:
        """
        Remove passed vehicles from both "vehicles_passed" and "turning_vehicles_passed"

        :param vehicles: vehicles that has passed
        :type vehicles: str
        :return: None
        """
        self._vehicles_passed.difference_update(vehicles)
        self._turning_vehicles['vehicles_passed'].difference_update(vehicles)

    """ SETTERS AND GETTERS """

    @property
    def passing_veh_n_s(self) -> int:
        """
        Traffic Light Info Storage  passing vehicles on NS direction getter

        :return: passing vehicles on NS
        :rtype: int
        """
        return self._passing_veh_n_s

    @property
    def passing_veh_e_w(self) -> int:
        """
        Traffic Light Info Storage  passing vehicles on EW direction getter

        :return: passing vehicles on EW
        :rtype: int
        """
        return self._passing_veh_e_w

    @property
    def waiting_time_veh_n_s(self) -> int:
        """
        Traffic Light Info Storage  waiting time on NS direction getter

        :return: waiting time vehicles on NS
        :rtype: int
        """
        return self._waiting_time_veh_n_s

    @property
    def waiting_time_veh_e_w(self) -> int:
        """
        Traffic Light Info Storage  waiting time on EW direction getter

        :return: waiting time vehicles on EW
        :rtype: int
        """
        return self._waiting_time_veh_e_w

    @property
    def vehicles_passed(self) -> set:
        """
        Traffic Light Info Storage  vehicles passed getter

        :return: vehicles passed
        :rtype: set
        """
        return self._vehicles_passed

    @property
    def turning_vehicles(self) -> dict:
        """
        Traffic Light Info Storage  turning vehicles getter
 
        :return: turning vehicles
        :rtype: dict
        """
        return self._turning_vehicles

    @property
    def roads(self) -> list:
        """
        Traffic Light Info Storage roads getter

        :return: roads ids
        :rtype: list
        """
        return self._roads

    @roads.setter
    def roads(self, roads: list) -> None:
        """
        Traffic Light Info Storage roads setter

        :param roads: roads names list
        :type roads: list
        :return: None
        """
        self._roads = roads

    @property
    def actual_program(self) -> str:
        """
        Traffic Light Info Storage  actual program getter

        :return: actual program
        :rtype: str
        """
        return self._actual_program

    @property
    def date_info(self) -> dict:
        """
        Traffic Light Info Storage date info getter

        :return: date info
        :rtype: dict
        """
        return self._date_info

    @date_info.setter
    def date_info(self, date_info: dict) -> None:
        """
        Traffic Light Info Storage date info setter

        :param date_info: date info
        :type date_info: dict
        :return: None
        """
        self._date_info = date_info
