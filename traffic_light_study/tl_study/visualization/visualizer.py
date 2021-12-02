from typing import Union

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


class Visualizer:
    """
    Class for visualizing the dataset information.
    """

    def __init__(self):
        """
        Visualizer class initializer
        """
        self._dataset = pd.DataFrame()

    def load_dataset(self, dataset_file: str):
        """
        Load dataset from a given directory.

        :param dataset_file: directory where the dataset is stored
        :type dataset_file: str
        :return: None
        """
        self._dataset = pd.read_csv(dataset_file)
        # Create new column with the accumulated time
        self._dataset['total_waiting_time'] = self._dataset['waiting_time_veh_n_s'] + self._dataset[
            'waiting_time_veh_e_w']

    def create_box_plot(self, x: str, y: str, hue: str, palette: Union[str, list]):
        """
        Create a box plot and show it.

        :param x: x-axis value
        :type x: str
        :param y: y-axis value
        :type y: str
        :param hue: hue for grouping data
        :type hue: str
        :param palette: palette used on the plot
        :type palette: str or list
        :return: None
        """
        sns.boxplot(x=x, y=y, hue=hue, data=self._dataset, palette=palette)
        plt.show()

    def create_scatter_plot(self, x: str, y: str, hue: str, palette: Union[str, list]):
        """
        Create a scatter plot and show it.

        :param x: x-axis value
        :type x: str
        :param y: y-axis value
        :type y: str
        :param hue: hue for grouping data
        :type hue: str
        :param palette: palette used on the plot
        :type palette: str or list
        :return: None
        """
        sns.scatterplot(x=x, y=y, hue=hue, data=self._dataset, palette=palette)
        plt.show()

    def create_pair_plot(self, hue: str, palette: Union[str, list], kind: str = 'scatter'):
        """
        Create a pair plot and show it.

        :param hue: hue for grouping data
        :type hue: str
        :param palette: palette used on the plot
        :type palette: str or list
        :param kind: Kind of the pair plot. Default is 'scatter'. Possible options are: scatter, kde, hist, reg
        :type kind: str
        :return: None
        """
        sns.pairplot(data=self._dataset, hue=hue, palette=palette, kind=kind)
        plt.show()

    def create_bar_plot(self, x: str, y: str, hue: str, palette: Union[str, list]):
        """
        Create a bar plot and show it.

        :param x: x-axis value
        :type x: str
        :param y: y-axis value
        :type y: str
        :param hue: hue for grouping data
        :type hue: str
        :param palette: palette used on the plot
        :type palette: str or list
        :return: None
        """
        sns.barplot(x=x, y=y, hue=hue, data=self._dataset, palette=palette)
        plt.show()

    def create_line_plot(self, x: str, y: str, hue: str, palette: Union[str, list]):
        """
        Create a line plot and show it.

        :param x: x-axis value
        :type x: str
        :param y: y-axis value
        :type y: str
        :param hue: hue for grouping data
        :type hue: str
        :param palette: palette used on the plot
        :type palette: str or list
        :return: None
        """
        sns.lineplot(x=x, y=y, hue=hue, data=self._dataset, palette=palette)
        plt.show()

    @property
    def dataset(self):
        return self._dataset
