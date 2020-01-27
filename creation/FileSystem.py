import os
from pathlib import Path
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


def create_directories_for(file_path: str) -> None:
    """
    Creates the directories of the given path if they're not already existing

    :param file_path: the path to the file which the directories should be created for
    """
    dir_path = os.path.dirname(file_path)
    if dir_path:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
