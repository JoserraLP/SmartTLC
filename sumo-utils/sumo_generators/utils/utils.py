def parse_to_valid_schema(input_info) -> str:
    """
    Parse the input to a valid middleware schema by replacing special characters

    :param input_info: input information
    :return: input string in valid format
    :rtype: str
    """
    return str(input_info).replace('\'', '\"').replace(" ", "")
