from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from tl_predictor.ml.base_classifier import BaseClassification


class NaiveBayes(BaseClassification):
    """
    Naive Bayes Classification algorithm
    """

    def __init__(self):
        """
        Naive Bayes class initializer
        """
        super().__init__()
        self._model = GaussianNB()


class SVM(BaseClassification):
    """
    Support Vector Machine Classification algorithm
    """

    def __init__(self, kernel: str, degree: int = -1):
        """
        Support Vector Machine class initializer

        :param kernel: algorithm kernel
        :type kernel: str
        :param degree: algorithm degree. Not available with 'linear' kernel. Default to -1
        :type kernel: int
        """
        super().__init__()
        if degree != -1:
            self._model = SVC(kernel=kernel, degree=degree)
        else:
            self._model = SVC(kernel=kernel)


class KNearestNeighbors(BaseClassification):
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
        self._model = KNeighborsClassifier(n_neighbors=num_neighbors)


class DecisionTree(BaseClassification):
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
        self._model = DecisionTreeClassifier(max_depth=max_depth)


class RandomForest(BaseClassification):
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
        self._model = RandomForestClassifier(n_estimators=num_estimators, max_depth=max_depth)
