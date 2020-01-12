from typing import Dict
import toml
import logging

from matcher.XlsxProcessor import XlsxProcessor
from matcher.XmlProcessor import XmlProcessor
from matcher.internal.debug.HtmlWriter import HtmlWriter
from classifier.BinClassifier import BinClassifier


class MatchingManager:

    __xlsx_handler: XlsxProcessor
    __xml_handler: XmlProcessor
    __config: Dict[str, str]
    __classifier: BinClassifier

    def __init__(self, config_path: str, log_file: str = "matching.log"):
        self.__classifier = BinClassifier()
        self.__config = self.__read_config(config_path)
        # configure logging
        logging.basicConfig(filename=log_file, level=logging.WARNING)

    def train(self, source_path: str, sink_path: str, nested_sink_dir: str = ""):
        self.__xml_handler = XmlProcessor(self.__classifier, self.__config)
        self.__xlsx_handler = XlsxProcessor(self.__classifier, self.__config, sink_path, nested_sink_dir)
        for pair_list in self.__xml_handler.read_xml(source_path):
            self.__xlsx_handler.match_given_values_in(pair_list)
        # digest the whole pile of data
        self.__classifier.train()

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

    def dump_classifier_matrix(self, file: str) -> None:
        # TODO: write some expressive docu here
        raw_data = self.__classifier.dump_raw_data()
        writer = HtmlWriter(raw_data)
        writer.dump_as_html(file)
