from abc import ABC, abstractmethod

from t_analyzer.providers.analyzer import TrafficAnalyzer
from t_predictor.providers.predictor import TrafficPredictor
from tl_controller.static.constants import TRAFFIC_TYPE_TL_ALGORITHMS


class AdaptationStrategy(ABC):
    """
    Adaptation Strategy interface that declares the operations common to all supported adaptation approaches.

    This interface is used by the Context to call the program defined by concrete strategies.
    """

    def __init__(self, traffic_light_id: str):
        """
        Adaptation Strategy constructor

        :param traffic_light_id: traffic light identifier
        :type traffic_light_id: dict
        """
        self._traffic_light_id = traffic_light_id

    @abstractmethod
    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        """
        Get new traffic light program based on traffic info

        :param traffic_info: traffic information
        :type traffic_info: dict
        :param timestep: simulation timestep. Default to None
        :type timestep: int
        :param temporal_window: temporal window identifier. Default to None
        :type temporal_window: int
        :return: new traffic light program
        :rtype: str
        """
        raise NotImplementedError


""" Concrete Adaptation Strategies"""


class StaticAS(AdaptationStrategy):
    """
    Static Adaptation Strategy not using any contextual information.
    Always behaves the same, returning the equally distributed traffic light program
    """

    def __init__(self, traffic_light_id: str):
        """
        SelfTrafficAnalyzer Adaptation Strategy
        """
        super().__init__(traffic_light_id)

    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        # Return equally distributed traffic light program
        return TRAFFIC_TYPE_TL_ALGORITHMS[str(int(len(list(TRAFFIC_TYPE_TL_ALGORITHMS.values()))/2))]


class SelfTrafficAnalyzerAS(AdaptationStrategy):
    """
    Self Traffic Analyzer Adaptation Strategy only uses its own traffic analyzer component
    """

    def __init__(self, analyzer: TrafficAnalyzer, traffic_light_id: str):
        """
        SelfTrafficAnalyzer Adaptation Strategy
        """
        super().__init__(traffic_light_id)
        self._analyzer = analyzer

    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        # Retrieve self traffic information
        traffic_light_info = traffic_info[self._traffic_light_id].get_traffic_analyzer_info(temporal_window=temporal_window)

        # There is only one junction, so retrieve its information
        current_traffic_type = self._analyzer.analyze_current_traffic_flow(
            passing_veh_n_s=traffic_light_info['passing_veh_n_s'],
            passing_veh_e_w=traffic_light_info['passing_veh_e_w'])

        return TRAFFIC_TYPE_TL_ALGORITHMS[str(int(current_traffic_type))]


class SelfTrafficPredictorAS(AdaptationStrategy):
    """
    Self Traffic Predictor Adaptation Strategy only uses its own traffic predictor component
    """

    def __init__(self, traffic_predictor: TrafficPredictor, traffic_light_id: str):
        """
        SelfTrafficPredictor Adaptation Strategy
        """
        super().__init__(traffic_light_id)
        self._traffic_predictor = traffic_predictor

    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        # Retrieve self traffic information
        traffic_light_info = traffic_info[self._traffic_light_id].get_traffic_predictor_info(temporal_window=temporal_window)

        # Predict the current traffic type
        current_traffic_type = self._traffic_predictor.predict_traffic_type(traffic_light_info)

        return TRAFFIC_TYPE_TL_ALGORITHMS[str(int(current_traffic_type))]


class SelfTrafficAnalyzerAndPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        pass


class SelfTrafficAnalyzerTurnPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        pass


class AdjacentTrafficAnalyzerAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        pass


class AdjacentTrafficPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        pass


class AdjacentTrafficAnalyzerAndPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        pass


class AdjacentTrafficAnalyzerTurnPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict, timestep: int = None, temporal_window: int = None) -> str:
        pass
