from __future__ import annotations
from typing import List, Tuple, Iterator, Dict
import re
import xml.etree.ElementTree as ElemTree

from classifier.BinClassifier import BinClassifier


class XmlProcessor:

    __classifier: BinClassifier
    __config: Dict[str, str]
    __targets: List[(str, List[(str, str)])]

    def __init__(self, sink: BinClassifier, config: Dict[str, str], path_to_source: str):
        """
        The constructor

        :param sink: the classifier to push the data into
        :param config: a dictionary holding config data
        :param path_to_source: the path to the xml file to read from (for matching)
        """
        self.__classifier = sink
        self.__config = config
        tree = ElemTree.parse(path_to_source)
        root = tree.getroot()
        src_nodes: List[ElemTree.Element] = []
        for node_name in self._get_main_node_names():
            found_nodes = root.findall(".//{}".format(node_name))
            src_nodes.extend(found_nodes)
        # continue with transforming the nodes into a list of tuples
        # TODO: pushing all to the stack is a waste of memory: use a generator instead

    def __iter__(self) -> XmlProcessor:
        return self

    def __next__(self) -> List[(str, str)]:
        # use a stack scheme as order is not relevant for the matching
        try:
            current: Tuple[str, List[(str, str)]] = self.__targets.pop()
            self.__classifier.add_source_path(current[0])
            return current[1]
        except IndexError:
            raise StopIteration

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
            for key in node.attr.keys():
                new_path = current_path + "/@{}".format(key)
                # self.__classifier.add_source_path(new_path)
                values = self._path_to_xml_values(new_path, parent_node)
                pairs = zip(values, ids)    # hope that it fails in case both lists are not equal in length
                self.__targets.append((new_path, list(pairs)))

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
                pairs = zip(values, ids)
                self.__targets.append((current_path, list(pairs)))
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
