from typing import List, Tuple, Iterator
from enum import Enum
import xml.etree.ElementTree as ElemTree
import toml
import re
from classifier.BinClassifier import BinClassifier


class XmlXlsxMatcher:

    class TableType(Enum):
        HORIZONTAL = 0
        VERTICAL = 1
        CROSS = 2

    FORWARDING_KEY = "forwarding_on"

    __config = {}
    __classifier = BinClassifier()
    __root_path: str
    __nested_xlsx_dir: str

    def __init__(self, path_to_config: str, path_root_xlsx: str, nested_xlsx_dir: str = "nested/"):
        """
        The constructor

        :param path_to_config: the path to the config file
        :param path_root_xlsx: the path to the main Excel file
        :param nested_xlsx_dir: the path to the other Excel files which the root file might reference to
        """
        self.__read_config(path_to_config)
        self.__root_path = path_root_xlsx
        root_file_name = re.search(r"\b\w*\.xlsx$", path_root_xlsx).group(0)
        root_path = path_root_xlsx[:-len(root_file_name)]
        if not nested_xlsx_dir.endswith("/"):
            nested_xlsx_dir += "/"
        self.__nested_xlsx_dir = root_path + nested_xlsx_dir

    def train(self, path_to_master_xml: str, path_to_slave_xlsx) -> None:
        # TODO: doc me
        tree = ElemTree.parse(path_to_master_xml)
        root = tree.getroot()
        for node in self._get_main_nodes():
            list_root = root.findall(".//{}".format(node))
            self._process_xml_master_nodes(list_root)

    def _axis_is_forwarding(self, name: str) -> bool:
        """
        Returns if the column (or row) references another Excel file which might be followed
        :param name: the identifier of the axis (column or row)
        :return: true if the program should open the file and search for data there
        """
        if self.FORWARDING_KEY not in self.__config:
            return False    # no forwarding specified
        if self.__config[self.FORWARDING_KEY] != name:
            return False
        return True

    def _process_xml_master_nodes(self, parent_node: ElemTree.Element):
        """
        Goes through the child list of the given node and treats them as master: meaning that the classifier will treat
        the xlsx as slave where the values from the xml has to be found in

        :param parent_node: the node which contains the list of nodes to match with the xlsx
        :return:
        """
        def process_attributes(node: ElemTree.Element, current_path: str, ids: List[str]) -> None:
            """
            Forwards the given attributes and their name to the function which tries to come up with matches

            :param node: the node which hosts the attributes
            :param current_path: the path to current node
            :param ids: the list of URI of all devices
            """
            for key in node.attr.keys():
                new_path = current_path + "/@{}".format(key)
                self.__classifier.add_source_path(new_path)
                values = self._path_to_xml_values(new_path, parent_node)
                pairs = zip(values, ids)    # hope that it fails in case both lists are not equal in length
                self._match_in_xslx(pairs)

        def process_node(node: ElemTree.Element, current_path: str, ids: List[str]) -> None:
            """
            Checks the given node for a value and attributes and forwards them to the function matching them to their
            counterpart in the xlsx. If the node contains child-nodes it processes recursively

            :param node: the node to extract the data (and children) from
            :param current_path: the path to the current node
            :param ids: the list of URI of all devices
            """
            if not node.text.isspace():
                self.__classifier.add_source_path(current_path)
                values = self._path_to_xml_values(current_path, parent_node)
                pairs = zip(values, ids)
                self._match_in_xslx(pairs)
            if node.attrib:
                process_attributes(node, current_path, ids)
            for child_node in node:
                name = child_node.tag
                process_node(child_node, current_path + "/{}".format(name), ids)

        identifier_list = []
        # get an overview about the targets to find
        for child in parent_node:
            # start with getting the identifier
            current_id = child.findall(".//{}".format(self._get_universal_id())).tag
            identifier_list.append(current_id)
        # use the first node as blue-print
        process_node(parent_node[0], "{}/{}".format(parent_node.tag, parent_node[0].tag), identifier_list)

    @staticmethod
    def _path_to_xml_values(path: str, root_node: ElemTree.Element) -> List[str]:
        """
        Resolves the given path to the nodes (or their attribute) of interest and returns the list of their values as
        they appear

        :param path: the path to resolve
        :param root_node: the node which contains the list of nodes eg. the node which is equivalent to the root of path
        :return: all values of the nodes or attributes under the given path
        """
        # as the path model is similar to XPath: just it
        result = re.search(r"(?<=@)\w*$", path)
        # cut away the root node
        root_end = path.index("/")
        node_path = path[root_end:]
        values = []
        if result is None:
            # means a node has to be processed
            nodes = root_node.findall(".{}".format(node_path))
            for node in nodes:
                values.append(node.text)
        else:
            # means a attribute has to be processed
            attribute_name = result.group(0)
            node_path = node_path[:-len(attribute_name) + 2]     # -1 for the "@" and -1 for the "/" before it
            nodes = root_node.findall(".{}".format(node_path))
            for node in nodes:
                values.append(node.attrib[attribute_name])
        return values

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

    def _match_in_xslx(self, values: Iterator[Tuple[str, str]]) -> None:
        pass
