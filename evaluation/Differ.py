import logging
import xml.etree.ElementTree as ElemTree
import toml
from typing import Dict

from creation.ConfigDict import config_from_file


class XmlDiffer:

    __sink: logging.Logger
    __log_path: str
    __config: Dict[str, str]

    def __init__(self, log_path: str, config_path: str):
        # TODO: write some nice docu here
        self.__log_path = log_path
        self.__sink = logging.getLogger("DiffLogger")
        fh = logging.FileHandler(self.__log_path)
        fh.setLevel(logging.ERROR)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        # create formatter and add it to the handlers
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        # add the handlers to logger
        self.__sink.addHandler(ch)
        self.__sink.addHandler(fh)
        self.__config = config_from_file(config_path)

    def compare(self, first_file: str, second_file) -> None:
        # TODO: I need some docu here
        print("Starting comparision of {} with {}. Writing results to {}".format(first_file, second_file,
                                                                                 self.__log_path))
        tree_1 = ElemTree.parse(first_file)
        tree_2 = ElemTree.parse(second_file)
        root_1 = tree_1.getroot()
        root_2 = tree_2.getroot()
        start_path = root_1.tag
        self._process_node(root_1, root_2, start_path)

    def _process_node(self, to_process_1: ElemTree.Element, to_process_2: ElemTree.Element, current_path: str) -> None:
        # TODO: your docu could stand right here
        def has_item_list(to_check: ElemTree.Element) -> bool:
            # TODO: doc me
            pass
        if to_process_1.tag in self.__config["ListNodes"]:
            # means the name needs to be extracted from both and then the same names need to be compared
            # return afterwards
            pass
        if not to_process_1.text.isspace() or not to_process_2.text.isspace():
            # if either one of them is not empty
            pass
        if to_process_1.attrib or to_process_2.attrib:
            # compare the attributes
            pass
        # check if it is a list of nodes with the same name or not
        needs_indexing = has_item_list(to_process_1)
        if needs_indexing:
            # TODO: find a way to compare them anyway -> update the path
            pass
        else:
            # just go deeper the rabbit hole -> update the path
            pass
