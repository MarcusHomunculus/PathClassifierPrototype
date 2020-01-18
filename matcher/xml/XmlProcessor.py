from __future__ import annotations
from typing import List, Tuple, Dict, Iterator, Set
import re
import xml.etree.ElementTree as ElemTree

from classifier.BinClassifier import BinClassifier
from matcher.clustering.ValueNamePair import ValueNamePair
from matcher.xml.generation.GeneratorStruct import GeneratorStruct


class XmlProcessor:

    __classifier: BinClassifier
    __config: Dict[str, str]
    __targets: List[(str, List[ValueNamePair])]
    __source_path: str
    __name_nodes: Set[str]

    def __init__(self, sink: BinClassifier, config: Dict[str, str]):
        """
        The constructor

        :param sink: the classifier to push the data into
        :param config: a dictionary holding config data
        """
        self.__classifier = sink
        self.__config = config
        self.__targets = []
        self.__source_path = ""
        self.__name_nodes = set()

    def __iter__(self) -> XmlProcessor:
        return self

    def __next__(self) -> List[ValueNamePair]:
        # use a stack scheme as order is not relevant for the clustering
        # -> switch to a generator in a "proper" implementation
        try:
            current: Tuple[str, List[ValueNamePair]] = self.__targets.pop()
            if not len(current[1]):
                raise AssertionError("Should not register path '{}' without any value-name pairs".format(current[0]))
            self.__classifier.add_source_path(self._replace_indexes(current[0]))
            return current[1]
        except IndexError:
            raise StopIteration

    def read_xml(self, path_to_source: str) -> Iterator[List[(str, str)]]:
        """
        Performs the parsing process of the given XML and prepares a list of value-name pair lists that can be pulled
        from the returned iterator

        :param path_to_source: the path to the xml file to read from (for clustering)
        :return: an iterator returning lists of value-name pairs list by list
        """
        self.__source_path = path_to_source
        tree = ElemTree.parse(self.__source_path)
        root = tree.getroot()
        for node in self._get_main_node_names():
            list_root = root.findall(".//{}".format(node))[0]
            self._process_xml_master_nodes(list_root)
        # continue with transforming the nodes into a list of tuples
        # advertise as iterator for lists of value-name-pairs
        return self

    def build_template(self, template_path: str):
        # TODO: write some nice docu here
        pass

    def write_xml(self, path_to_file: str) -> None:
        # TODO: write some nice docu here
        pass

    @staticmethod
    def group_target_paths(unsorted_paths: List[str]) -> List[GeneratorStruct]:
        # first insert the name paths
        # -> use the paths to form groups -> sort by node depth -> attributes after their node
        pass

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
                values = self._path_to_xml_values(new_path, parent_node)
                self.__targets.append((new_path, ValueNamePair.zip(values, ids)))

        def iterate_by_index(node: ElemTree.Element, current_path: str, ids: List[str]) -> None:
            """
            Iterates through the child nodes of the given node supported by an index which is useful if all nodes carry
            the same name

            :param node: the node of which the children shall be analyzed
            :param current_path: the current path for the classifier
            :param ids: the list of URIs
            """
            # the indexing starts with 1: https://docs.python.org/3.8/library/xml.etree.elementtree.html#example
            child_index = 1
            for child_node in node:
                process_node(child_node, current_path + "/{}[{}]".format(child_node.tag, child_index), ids)
                child_index += 1

        def iterate_by_name(node: ElemTree.Element, current_path: str, ids: List[str]) -> None:
            """
            Iterates over the children of the node assuming that they're all unique in their name under their siblings

            :param node: the node of which the children shall be analyzed
            :param current_path: the current path for the classifier
            :param ids: the list of URIs
            """
            for child_node in node:
                name = child_node.tag
                if name == self._get_universal_id():
                    name_path = "{}/{}".format(current_path, name)
                    # rely on the uniqueness provided by the set
                    self.__name_nodes.add(name_path)
                    # makes no sense to search for pairs of the same two names
                    continue
                process_node(child_node, current_path + "/{}".format(name), ids)

        def process_node(node: ElemTree.Element, current_path: str, ids: List[str]) -> None:
            """
            Checks the given node for a value and attributes and forwards them to the function clustering them to their
            counterpart in the xlsx. If the node contains child-nodes it processes recursively

            :param node: the node to extract the data (and children) from
            :param current_path: the path to the current node
            :param ids: the list of URI of all devices
            """
            if not node.text.isspace():
                values = self._path_to_xml_values(current_path, parent_node)
                if len(values) == len(ids):
                    # if not enough values are available a meaningful clustering is not possible anymore
                    self.__targets.append((current_path, ValueNamePair.zip(values, ids)))
            if node.attrib:
                process_attributes(node, current_path, ids)
            needs_indexing = XmlProcessor._has_same_name_children(node)
            # continue with going down deeper the tree -> if things get more complicated wrap these in separate
            # functions
            if needs_indexing:
                iterate_by_index(node, current_path, ids)
            else:
                iterate_by_name(node, current_path, ids)

        # get an overview about the targets to find
        identifier_list = list(map(lambda x: x.text, parent_node.findall(".//{}".format(self._get_universal_id()))))
        if len(identifier_list) < 1:
            raise AssertionError("No name extracted! Maybe wrong URI value in config file: " + self._get_universal_id())
        # use the first node as blue-print
        process_node(parent_node[0], "{}/{}".format(parent_node.tag, parent_node[0].tag), identifier_list)

    def _get_universal_id(self):
        """
        Returns the identifier which is used to distinguish the main nodes from each other

        :return: the identifier which can be used for clustering
        """
        return self.__config["uri"]

    def _get_main_node_names(self) -> List[str]:
        """
        Extracts the names of the anchor nodes in the XML from the config

        :return: an iterable of the nodes which should be trained
        """
        raw_list = self.__config["List_nodes"]
        return raw_list.split(",")

    @staticmethod
    def _path_to_xml_values(path: str, root_node: ElemTree.Element) -> List[str]:
        """
        Resolves the given path to the nodes (or their attribute) of interest and returns the list of their values as
        they appear

        :param path: the path to resolve
        :param root_node: the node which contains the list of nodes eg. the node which is equivalent to the root of path
        :return: all values of the nodes or attributes under the given path
        """
        # as the path model is similar to XPath: so just use it
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

    @staticmethod
    def _has_same_name_children(to_test: ElemTree.Element) -> bool:
        """
        Iterates over the child nodes of the given node and checks if they have the same (tag-) name. It is assumed
        that nodes have either only different names or all carry the same name (this is **only** true for the mock
        data)

        :param to_test: the node to test for it's child names
        :return: True if children have a same name else False
        """
        name_list = []
        for child_node in to_test:
            name_list.append(child_node.tag)
        if len(name_list) < 2:
            return False
        # check if the child nodes have all the same name -> actually just pick the first 2 and assume the rest
        if name_list[0] != name_list[1]:
            return False
        return True

    @staticmethod
    def _replace_indexes(path_str: str) -> str:
        """
        Replaces all occurrences of an integer index with a general / abstract indexing notation ('[i]') and returns the
        result

        :param path_str: the path to check for integer indexes
        :return: the "clean" path only holding abstract indexes if any at all
        """
        return re.sub(r"\[\d.?]", "[i]", path_str)
