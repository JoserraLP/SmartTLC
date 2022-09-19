def parse_str_to_valid_schema(input_info: str) -> str:
    """
    Parse the input string to a valid middleware schema by replacing special characters

    :param input_info: input string
    :type input_info: str
    :return: input string in valid format
    :rtype: str
    """
    return str(input_info).replace('\'', '\"').replace(" ", "")