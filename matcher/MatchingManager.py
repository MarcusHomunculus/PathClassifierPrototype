from typing import Dict, List
import logging

from matcher.xlsx.XlsxProcessor import XlsxProcessor
from matcher.xml.XmlProcessor import XmlProcessor
from matcher.xml.generation.GeneratorCluster import ValuePathStruct, PathCluster
from matcher.visualization.HtmlWriter import HtmlWriter
from classifier.PathClassifier import PathClassifier
from creation.FileSystem import create_directories_for, config_from_file


class MatchingManager:

    __xlsx_handler: XlsxProcessor
    __xml_handler: XmlProcessor
    __config: Dict[str, str]
    __classifier: PathClassifier
    # store these files to bind them to the program
    __source_path: str
    __sink_path: str
    __nested_sink_dir: str
    __template_path: str
    __path_dict: Dict[str, str]

    def __init__(self, config_path: str, log_file: str = "clustering.log"):
        """
        The constructor

        :param config_path: the path to the config (toml-) file
        :param log_file: the file path under which to store the log file
        """
        self.__classifier = PathClassifier()
        self.__config = config_from_file(config_path)
        # prepare the "workspace" for the log
        create_directories_for(log_file)
        # configure logging
        logging.basicConfig(filename=log_file, level=logging.WARNING)

    def train(self, source_path: str, sink_path: str, nested_sink_dir: str = "") -> None:
        """
        Manages the training process for the classifier by feeding it with data and letting the classifier evaluate the
        data

        :param source_path: the path of the source (XML-) file
        :param sink_path: the path of the sink (xlsx-) file
        :param nested_sink_dir: the path under which forwarded files can be found
        """
        self.__sink_path = sink_path
        self.__nested_sink_dir = (nested_sink_dir + "/") if not nested_sink_dir.endswith("/") else nested_sink_dir
        self.__source_path = source_path
        self.__xml_handler = XmlProcessor(self.__classifier, self.__config)
        self.__xlsx_handler = XlsxProcessor(self.__classifier, self.__config, self.__sink_path, self.__nested_sink_dir)
        for pair_list in self.__xml_handler.read_xml(self.__source_path):
            self.__xlsx_handler.match_given_values_in(pair_list)
        # digest the whole pile of data
        self.__classifier.train()
        # due to the tree structure of the XML it makes more sense that the XmlProcessor gives the structure and the
        # XlsxProcessor acts only as server
        self.__path_dict = {y: x for x, y in self.__classifier.to_dict().items()}
        # check there isn't any path which has multiple index identifiers -> this would probably require recursive
        # GeneratorStructs which aren't at hand
        for path in self.__path_dict.keys():
            if path.count("[i]") > 1:
                raise AssertionError("Do not have the means to treat complex paths like '{}'! Aborting".format(path))

    def create_build_environment(self, template_path: str) -> None:
        """
        Creates the files which are required to build a XML-file from "scratch"

        :param template_path: the path under which the XML-template can be stored
        """
        self.__template_path = template_path
        self.__xml_handler.build_template(self.__source_path, self.__template_path)

    def generate(self, new_file_path: str) -> int:
        """
        Creates a new XML-file from the xlsx-files it learned from under the given path

        :param new_file_path: the path under which to store the result
        :return: the number of nodes added to the generated file
        """
        # the XML-modules knows their paths best -> so let it do some meaningful ordering of their paths
        target_classes = self.__xml_handler.group_target_paths(list(self.__path_dict.keys()))
        # group the ValuePathStructs by classes in separate lists -> TODO: their could be a more elegant way?
        cluster_list: List[List[PathCluster]] = []
        class_index = 0
        for target_class in target_classes:
            cluster_list.append([])
            target_names = self.__xlsx_handler.get_names(self._translate_to_xlsx_name_path(target_class.root_path))
            for name in target_names:
                current = PathCluster(name, target_class.name_path, target_class.root_path)
                for source_path in target_class.node_paths:
                    values = self.__xlsx_handler.receive_for_path(self.__path_dict[source_path], name,
                                                                  self.__nested_sink_dir)
                    current.add_pair(ValuePathStruct(name, values, source_path))
                cluster_list[class_index].append(current)
            class_index += 1
        return self.__xml_handler.write_xml(new_file_path, self.__template_path, cluster_list)

    def _translate_to_xlsx_name_path(self, xml_base_path: str) -> str:
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
