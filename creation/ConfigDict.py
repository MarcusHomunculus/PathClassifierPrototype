from typing import Dict
import toml


def config_from_file(path_to_file: str) -> Dict[str, str]:
    """
    Reads in the config file

    :param path_to_file: the path to the TOML file to read
    :return: the key-value-pairs extracted from the config file
    """
    config = {}
    with open(path_to_file, "r", encoding="utf-8") as c:
        config.update(toml.load(c))
    return config
