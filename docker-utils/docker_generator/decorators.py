from functools import wraps
from docker_structure import ALL_CONTAINERS


def check_containers(func):
    """Decorator for checking valid containers"""
    @wraps(func)
    def wrapper_check_container(*args, **kwargs):
        # Check if all the values are False, meaning that the containers provided does not exists
        if any([container in ALL_CONTAINERS.keys() for container in kwargs['containers']]):
            func(*args, **kwargs)
        else:
            print(f"Error, please insert a valid container. \nOptions are {list(ALL_CONTAINERS.keys())}")
            raise ValueError

    return wrapper_check_container
