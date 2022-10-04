from abc import ABC, abstractmethod

from t_analyzer.providers.analyzer import TrafficAnalyzer
from t_predictor.providers.predictor import TrafficPredictor
from tl_controller.static.constants import TRAFFIC_TYPE_TL_ALGORITHMS


class AdaptationStrategy(ABC):
    """
    Adaptation Strategy interface that declares the operations common to all supported adaptation approaches.

    This interface is used by the Context to call the program defined by concrete strategies.
    """

    @abstractmethod
    def get_new_tl_program(self, traffic_info: dict) -> str:
        """
        Get new traffic light program based on traffic info

        :param traffic_info: traffic information
        :type traffic_info: dict
        :return: new traffic light program
        :rtype: str
        """
        raise NotImplementedError


""" Concrete Adaptation Strategies"""


class StaticAS(AdaptationStrategy):

    def __init__(self):
        """
        SelfTrafficAnalyzer Adaptation Strategy
        """

    def get_new_tl_program(self, traffic_info: dict) -> str:
        return TRAFFIC_TYPE_TL_ALGORITHMS[str(int(len(list(TRAFFIC_TYPE_TL_ALGORITHMS.values()))/2))]


class SelfTrafficAnalyzerAS(AdaptationStrategy):

    def __init__(self, analyzer: TrafficAnalyzer):
        """
        SelfTrafficAnalyzer Adaptation Strategy
        """
        self._analyzer = analyzer

    def get_new_tl_program(self, traffic_info: dict) -> str:
        # There is only one junction, so retrieve its information
        current_traffic_type = self._analyzer.analyze_current_traffic_flow(
            passing_veh_n_s=traffic_info['passing_veh_n_s'],
            passing_veh_e_w=traffic_info['passing_veh_e_w'])

        return TRAFFIC_TYPE_TL_ALGORITHMS[str(int(current_traffic_type))]


class SelfTrafficPredictorAS(AdaptationStrategy):

    def __init__(self, traffic_predictor: TrafficPredictor):
        """
        SelfTrafficPredictor Adaptation Strategy
        """
        self._traffic_predictor = traffic_predictor

    def get_new_tl_program(self, traffic_info: dict) -> str:
        current_traffic_type = self._traffic_predictor.predict_traffic_type(traffic_info)
        return TRAFFIC_TYPE_TL_ALGORITHMS[str(int(current_traffic_type))]


class SelfTrafficAnalyzerAndPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict) -> str:
        pass


class SelfTrafficAnalyzerTurnPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict) -> str:
        pass


class AdjacentTrafficAnalyzerAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict) -> str:
        pass


class AdjacentTrafficPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict) -> str:
        pass


class AdjacentTrafficAnalyzerAndPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict) -> str:
        pass


class AdjacentTrafficAnalyzerTurnPredictorAS(AdaptationStrategy):

    def get_new_tl_program(self, traffic_info: dict) -> str:
        pass
