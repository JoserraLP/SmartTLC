from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

import seaborn as sns

from tl_predictor.ml.base_classifier import BaseClassification


class NaiveBayes(BaseClassification):
    def __init__(self):
        super().__init__()
        self._model = GaussianNB()


class SVM(BaseClassification):
    def __init__(self, kernel: str, degree: int = -1):
        super().__init__()
        if degree != -1:
            self._model = SVC(kernel=kernel, degree=degree)
        else:
            self._model = SVC(kernel=kernel)


class KNearestNeighbors(BaseClassification):
    def __init__(self, num_neighbors: int = 1):
        super().__init__()
        self._model = KNeighborsClassifier(n_neighbors=num_neighbors)


class DecisionTree(BaseClassification):
    def __init__(self, max_depth: int = 2):
        super().__init__()
        self._model = DecisionTreeClassifier(max_depth=max_depth)


class RandomForest(BaseClassification):
    def __init__(self, num_estimators: int = 5, max_depth: int = 2):
        super().__init__()
        self._model = RandomForestClassifier(n_estimators=num_estimators, max_depth=max_depth)
