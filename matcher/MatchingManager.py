from typing import List, Tuple, Dict
import toml

from matcher.XlsxProcessor import XlsxProcessor
from classifier.BinClassifier import BinClassifier


class MatchingManager:

    __xlsx_handler: XlsxProcessor
    __config: Dict[str, str]
    __classifier: BinClassifier

    def __init__(self, config_path: str, root_xlsx_path: str, nested_xlsx_dir: str):
        self.__classifier = BinClassifier()
        self.__config = self.__read_config(config_path)
        self.__xlsx_handler = XlsxProcessor(self.__classifier, self.__config, root_xlsx_path, nested_xlsx_dir)

    def match_in_xlsx_sink(self, value_name_pairs: List[Tuple[str, str]]) -> None:
        # TODO: write some nice docu here
        self.__xlsx_handler.match_given_values_in(self.mock_test_data())

    @staticmethod
    def mock_test_data():
        value_name_pairs = [
            ("warehouseman", "pedantic jackson"),
            ("engineer", "nostalgic curie"),
            ("electrician", "trusting stonebraker")
        ]
        return value_name_pairs

    @staticmethod
    def __read_config(path_to_file: str) -> Dict[str, str]:
        """
        Reads in the config file

        :param path_to_file: the path to the TOML file to read
        :return: the key-value-pairs extracted from the config file
        """
        config = {}
        with open(path_to_file, "r", encoding="utf-8") as c:
            config.update(toml.load(c))
        return config

