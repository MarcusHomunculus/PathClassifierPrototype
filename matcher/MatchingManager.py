from typing import List, Tuple, Dict
import toml

from matcher.XlsxProcessor import XlsxProcessor
from matcher.XmlProcessor import XmlProcessor
from classifier.BinClassifier import BinClassifier


class MatchingManager:

    __xlsx_handler: XlsxProcessor
    __xml_handler: XmlProcessor
    __config: Dict[str, str]
    __classifier: BinClassifier

    def __init__(self, config_path: str):
        self.__classifier = BinClassifier()
        self.__config = self.__read_config(config_path)

    def train(self, source_path: str, sink_path: str, nested_sink_dir: str = ""):
        self.__xml_handler = XmlProcessor(self.__classifier, self.__config)
        self.__xlsx_handler = XlsxProcessor(self.__classifier, self.__config, sink_path, nested_sink_dir)
        for pair_list in self.__xml_handler.read_xml(source_path):
            self.__xlsx_handler.match_given_values_in(pair_list)

    @staticmethod
    def __mock_test_data():
        value_name_pairs = [
            ("warehouseman", "pedantic jackson"),
            ("engineer", "nostalgic curie"),
            ("electrician", "trusting stonebraker")
        ]
        return value_name_pairs

    @staticmethod
    def __mock_test_cross_data():
        value_name_pairs = [
            ("pedantic jackson", "Logistics"),
            ("nostalgic curie", "Research and Development"),
            ("trusting stonebraker", "Production")
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

