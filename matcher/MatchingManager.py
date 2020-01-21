from typing import Dict
import toml
import logging

from matcher.xlsx.XlsxProcessor import XlsxProcessor
from matcher.xml.XmlProcessor import XmlProcessor
from matcher.xml.generation.GeneratorStruct import GeneratorStruct
from matcher.visualization.HtmlWriter import HtmlWriter
from classifier.BinClassifier import BinClassifier


class MatchingManager:

    __xlsx_handler: XlsxProcessor
    __xml_handler: XmlProcessor
    __config: Dict[str, str]
    __classifier: BinClassifier
    # store these files to bind them to the program
    __sink_path: str
    __nested_sink_dir: str
    __template_path: str
    __path_dict: Dict[str, str]

    def __init__(self, config_path: str, log_file: str = "clustering.log"):
        # TODO: here's some docu missing
        self.__classifier = BinClassifier()
        self.__config = self.__read_config(config_path)
        # configure logging
        logging.basicConfig(filename=log_file, level=logging.WARNING)

    def train(self, source_path: str, sink_path: str, nested_sink_dir: str = ""):
        # TODO: doc me
        self.__sink_path = sink_path
        self.__nested_sink_dir = (nested_sink_dir + "/") if not nested_sink_dir.endswith("/") else nested_sink_dir
        self.__xml_handler = XmlProcessor(self.__classifier, self.__config)
        self.__xlsx_handler = XlsxProcessor(self.__classifier, self.__config, self.__sink_path, self.__nested_sink_dir)
        for pair_list in self.__xml_handler.read_xml(source_path):
            self.__xlsx_handler.match_given_values_in(pair_list)
        # digest the whole pile of data
        self.__classifier.train()
        # due to the tree structure of the XML it makes more sense that the XmlProcessor gives the structure and the
        # XlsxProcessor acts only as server
        self.__path_dict = {y: x for x, y in self.__classifier.to_dict().items()}
        # generate the template

    def generate(self, new_file_path: str):
        # TODO: your docu could stand right here
        # the XML-modules knows their paths best -> so let it do some meaningful ordering of their paths
        target_classes = self.__xml_handler.group_target_paths(list(self.__path_dict.keys()))
        for target_class in target_classes:
            target_names = self.__xlsx_handler.get_names(self.translate_to_xlsx_name_path(target_class.root_path))
            for name in target_names:
                for source_path in target_class.node_paths:
                    values = self.__xlsx_handler.receive_for_path(self.__path_dict[source_path], name,
                                                                  self.__nested_sink_dir)
                    hello = "world"
        # for source_class in self.__xlsx_handler.get_names(list(path_data.values())):
        #     # TODO: create the node here -> create a function that expects the type to generate
        #   for path in target_paths:
        #        # TODO: construct the objects
        #        pass

    def translate_to_xlsx_name_path(self, xml_base_path: str) -> str:
        """
        Takes the given xml path and translates it to a name path for the given source-file-class the base path is
        addressing

        :param xml_base_path: the base-path(!) for a class in the source file
        :return: a corresponding name path in the sink file
        """
        # just pick one entry -> all paths for the sink file have a name path anyway
        # TODO: their should be a way to get the same information with less resources
        # the classifier-dict is sink_path : source_path
        transmuted = {y: x for x, y in self.__classifier.to_dict().items()}
        for key in transmuted:
            if xml_base_path in key:
                return XlsxProcessor.extract_name_path(transmuted[key])
        raise AttributeError("Could not find a match for '{}' in the source path set".format(xml_base_path))

    def dump_classifier_matrix(self, file: str) -> None:
        """
        Creates a **firefox** compatible html document illustrating the matches of the classifier

        :param file: the file to write the HTML data into
        """
        raw_data = self.__classifier.dump_raw_data()
        writer = HtmlWriter(raw_data)
        writer.dump_as_html(file)

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
