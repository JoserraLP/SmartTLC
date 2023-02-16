from traci._trafficlight import Logic, Phase


def parse_to_valid_schema(input_info) -> str:
    """
    Parse the input to a valid middleware schema by replacing special characters

    :param input_info: input information
    :return: input string in valid format
    :rtype: str
    """
    return str(input_info).replace('\'', '\"').replace(" ", "")


def parse_traffic_light_logic_to_str(tl_program: Logic) -> str:
    """
    Parse from traffic light Logic to str representing a list of phases with its duration and state split by ';'

    :param tl_program: traffic light program Logic
    :type tl_program: Logic

    :return: string representing a list of phases split by ';'
    :rtype: str
    """
    return ';'.join([f"{phase.state},{phase.duration}" for phase in tl_program.getPhases()])
