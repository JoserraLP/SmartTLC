import seaborn as sns

from typing import Union


def generate_random_palette(n_colors: int) -> list:
    """
    Generate a random palette with a given number of colors.

    :param n_colors: number of palette colors
    :type n_colors: int
    :return: list of RGB tuples
    :rtype: list
    """
    return sns.color_palette('Paired', n_colors=n_colors)


def set_theme(style: str, palette: Union[str, list], n_colors: int) -> None:
    """
    Set theme into the seaborn instance.

    :param style: define the style of the theme
    :type style: str
    :param palette: define the palette that will be used
    :type palette: str or list
    :param n_colors: number of palette colors
    :type n_colors: int
    :return: None
    """
    sns.set_palette(palette=palette, n_colors=n_colors)
    sns.set_theme(style=style, palette=palette)
