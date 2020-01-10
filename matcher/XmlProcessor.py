from __future__ import annotations
from typing import List, Tuple, Dict, Iterator
import re
import xml.etree.ElementTree as ElemTree

from classifier.BinClassifier import BinClassifier
from matcher.internal.data_struct.ValueNamePair import ValueNamePair


class XmlProcessor:

    __classifier: BinClassifier
    __config: Dict[str, str]
    __targets: List[(str, List[ValueNamePair])]

    def __init__(self, sink: BinClassifier, config: Dict[str, str]):
        """
        The constructor

        :param sink: the classifier to push the data into
        :param config: a dictionary holding config data
        """
        self.__classifier = sink
        self.__config = config
        self.__targets = []

    def __iter__(self) -> XmlProcessor:
        return self

    def __next__(self) -> List[ValueNamePair]:
        # use a stack scheme as order is not relevant for the matching
        # -> switch to a generator in a "proper" implementation
        try:
            current: Tuple[str, List[(str, str)]] = self.__targets.pop()
            if not len(current[1]):
                raise AssertionError("Should not register path '{}' without any value-name pairs".format(current[0]))
            self.__classifier.add_source_path(current[0])
            return current[1]
        except IndexError:
            raise StopIteration

    def read_xml(self, path_to_source: str) -> Iterator[List[(str, str)]]:
        """
        Performs the parsing process of the given XML and prepares a list of value-name pair lists that can be pulled
        from the returned iterator

        :param path_to_source: the path to the xml file to read from (for matching)
        :return: an iterator returning lists of value-name pairs list by list
        """
        tree = ElemTree.parse(path_to_source)
        root = tree.getroot()
        for node in self._get_main_node_names():
            list_root = root.findall(".//{}".format(node))[0]
            self._process_xml_master_nodes(list_root)
        # continue with transforming the nodes into a list of tuples
        # advertise as iterator for lists of value-name-pairs
        return self

    def _process_xml_master_nodes(self, parent_node: ElemTree.Element) -> None:
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
            for key in node.attrib.keys():
                new_path = current_path + "/@{}".format(key)
                # self.__classifier.add_source_path(new_path)
                values = self._path_to_xml_values(new_path, parent_node)
                self.__targets.append((new_path, ValueNamePair.zip(values, ids)))

        def process_node(node: ElemTree.Element, current_path: str, ids: List[str]) -> None:
            """
            Checks the given node for a value and attributes and forwards them to the function matching them to their
            counterpart in the xlsx. If the node contains child-nodes it processes recursively

            :param node: the node to extract the data (and children) from
            :param current_path: the path to the current node
            :param ids: the list of URI of all devices
            """
            if not node.text.isspace():
                values = self._path_to_xml_values(current_path, parent_node)
                self.__targets.append((current_path, ValueNamePair.zip(values, ids)))
            if node.attrib:
                process_attributes(node, current_path, ids)
            for child_node in node:
                name = child_node.tag
                if name == self._get_universal_id():
                    # makes no sense to search for pairs of the same two names
                    continue
                process_node(child_node, current_path + "/{}".format(name), ids)

        # get an overview about the targets to find
        identifier_list = list(map(lambda x: x.text, parent_node.findall(".//{}".format(self._get_universal_id()))))
        if len(identifier_list) < 1:
            raise AssertionError("No name extracted! Maybe wrong URI value in config file: " + self._get_universal_id())
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
            if len(nodes) < 1:
                raise AssertionError("Path '.{} yielded no results".format(node_path))
            for node in nodes:
                values.append(node.text)
        else:
            # means a attribute has to be processed
            attribute_name = result.group(0)
            node_path = node_path[:-(len(attribute_name) + 2)]     # -1 for the "@" and -1 for the "/" before it
            nodes = root_node.findall(".{}".format(node_path))
            if len(nodes) < 1:
                raise AssertionError("Path '.{} yielded no results".format(node_path))
            for node in nodes:
                values.append(node.attrib[attribute_name])
        return values

    def _get_universal_id(self):
        """
        Returns the identifier which is used to distinguish the main nodes from each other

        :return: the identifier which can be used for matching
        """
        return self.__config["uri"]

    def _get_main_node_names(self) -> List[str]:
        """
        Extracts the names of the anchor nodes in the XML from the config

        :return: an iterable of the nodes which should be trained
        """
        raw_list = self.__config["List_nodes"]
        return raw_list.split(",")
