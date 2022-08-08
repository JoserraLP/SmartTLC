from t_analyzer.providers.analyzer import TrafficAnalyzer
from t_analyzer.static.constants import DEFAULT_TEMPORAL_WINDOW, MQTT_URL, MQTT_PORT
import argparse


def get_options():
    """
    Get options from the execution command

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Traffic analyzer script.')

    # Define the arguments options
    arg_parser.add_argument('-t', '--temporal-window', dest='temporal_window', action='store',
                            default=DEFAULT_TEMPORAL_WINDOW, type=float,
                            help='define the traffic monitoring temporal window. '
                                 f'Default is {DEFAULT_TEMPORAL_WINDOW}.')

    arg_parser.add_argument("--middleware_host", dest="mqtt_url", action="store", default=MQTT_URL, type=str,
                               help=f"middleware broker host. Default is {MQTT_URL}.")
    arg_parser.add_argument("--middleware_port", dest="mqtt_port", action="store", default=MQTT_PORT, type=str,
                               help=f"middleware broker port. Default is {MQTT_PORT}.")

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":
    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Start traffic analyzer
    analyzer = TrafficAnalyzer(mqtt_url=exec_options.mqtt_url, mqtt_port=exec_options.mqtt_port,
                               temporal_window=exec_options.temporal_window)
