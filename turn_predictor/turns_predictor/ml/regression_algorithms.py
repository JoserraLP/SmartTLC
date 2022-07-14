from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from turns_predictor.ml.base_regressor import BaseRegression


class LRegression(BaseRegression):
    """
    Naive Bayes Classification algorithm
    """

    def __init__(self):
        """
        Naive Bayes class initializer
        """
        super().__init__()
        self._model = LinearRegression()


class KNearestNeighbors(BaseRegression):
    """
    K Nearest Neighbors Classification algorithm
    """
    def __init__(self, num_neighbors: int = 1):
        """
        KNN class initializer

        :param num_neighbors: number of neighbors. Default to 1
        :type num_neighbors: int
        """
        super().__init__()
        self._model = KNeighborsRegressor(n_neighbors=num_neighbors)


class DecisionTree(BaseRegression):
    """
    Decision Tree Classification algorithm
    """
    def __init__(self, max_depth: int = 2):
        """
        KNN class initializer

        :param max_depth: maximum depth of the tree. Default to 2
        :type max_depth: int
        """
        super().__init__()
        self._model = DecisionTreeRegressor(max_depth=max_depth)


class RandomForest(BaseRegression):
    """
    Random Forest Classification algorithm
    """
    def __init__(self, num_estimators: int = 5, max_depth: int = 2):
        """
        Random Forest class initializer

        :param num_estimators: number of decision trees. Default to 5
        :type num_estimators: int
        :param max_depth: maximum depth. Default to 2
        :type max_depth: int
        """
        super().__init__()
        self._model = RandomForestRegressor(n_estimators=num_estimators, max_depth=max_depth)
