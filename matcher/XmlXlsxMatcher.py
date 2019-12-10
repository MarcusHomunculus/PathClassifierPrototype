from typing import List, Tuple
from enum import Enum
import xml.etree.ElementTree as ElemTree
import toml
from classifier.BinClassifier import BinClassifier


class XmlXlsxMatcher:

    class TableType(Enum):
        HORIZONTAL = 0
        VERTICAL = 1
        CROSS = 2

    FORWARDING_KEY = "forwarding_on"

    __config = {}
    __classifier = BinClassifier()

    def __init__(self, path_to_config: str, path_root_xlsx: str, nested_xlsx_dir: str = "."):
        """
        The constructor

        :param path_to_config: the path to the config file
        :param path_root_xlsx: the path to the main Excel file
        :param nested_xlsx_dir: the path to the other Excel files which the root file might reference to
        """
        self.__read_config(path_to_config)

    def train(self, path_to_master_xml: str, path_to_slave_xlsx) -> None:
        # TODO: doc me
        tree = ElemTree.parse(path_to_master_xml)
        root = tree.getroot()
        for node in self._get_main_nodes():
            list_root = root.findall(".//{}".format(node))
            self._process_xml_master_nodes(list_root, path_to_slave_xlsx)

    def _axis_is_forwarding(self, name: str) -> bool:
        """
        Returns if the column (or row) references another Excel file which might be followed
        :param name: the identifier of the axis (column or row)
        :return: true if the program should open the file and search for data there
        """
        if XmlXlsxMatcher.FORWARDING_KEY not in self.__config:
            return False    # no forwarding specified
        if self.__config[XmlXlsxMatcher.FORWARDING_KEY] != name:
            return False
        return True

    def _process_xml_master_nodes(self, parent_node: ElemTree.Element, path_to_xlsx: str):
        # TODO: doc me
        def _process_attributes(node: ElemTree.Element, current_path: str, ids: List[str]) -> None:
            # TODO: write some nice docu here
            attr = node.attrib
            if not attr:
                # means the dict is empty -> nothing to do
                return
            for key in attr.keys():
                new_path = current_path + "/@{}".format(key)
                self.__classifier.add_source_path(new_path)
                values = self._path_to_xml_values(new_path)
                pairs = zip(values, ids)    # hope that it fails in case both lists are not equal in length
                self._match_values_to_xlsx_paths(pairs)
                # TODO: continue here

        identifier_list = []
        # get an overview about the targets to find
        for child in parent_node:
            # start with getting the identifier
            current_id = child.findall(".//{}".format(self._get_universal_id())).tag
            identifier_list.append(current_id)
        # use the first node as blue print
        for i in range(len(list(parent_node[0]))):
            pass

        # TODO: this is old: maybe there's something in there which can be reused?
        for child in parent_node:
            for element in child:
                name = element.tag
                if name == self._get_universal_id():
                    # skip this one as it has no additional data
                    continue
                val = str(element)
                attributes = element.attrib
                if not attributes:
                    pass

    def _path_to_xml_values(self, path: str, root_node: ElemTree.Element) -> List[str]:
        pass

    def _match_values_to_xlsx_paths(self, value_name_pairs: List[Tuple[str, str]]) -> List[str]:
        pass

    def _guess_table_structure(self, id_list: List[str]):
        pass

    def _get_main_nodes(self) -> List[str]:
        """
        Extracts the names of the anchor nodes in the XML from the config

        :return: an iterable of the nodes which should be trained
        """
        raw_list = self.__config["List_nodes"]
        return raw_list.split(",")

    def _get_universal_id(self):
        """
        Returns the identifier which is used to distinguish the main nodes from each other

        :return: the identifier which can be used for matching
        """
        return self.__config["uri"]

    def __read_config(self, path_to_file: str) -> None:
        """
        Reads in the config file

        :param path_to_file: the path to the TOML file to read
        """
        config = {}
        with open(path_to_file, "r", encoding="utf-8") as c:
            config.update(toml.load(c))
        self.__config = config

