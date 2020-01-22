from __future__ import annotations
from typing import List, Tuple, Dict, Iterator, Set
import re
import xml.etree.ElementTree as ElemTree
from pathlib import Path
import os
from xml.dom import minidom
import copy

from classifier.BinClassifier import BinClassifier
from matcher.clustering.ValueNamePair import ValueNamePair
from matcher.xml.generation.GeneratorCluster import GeneratorStruct, PathCluster, ValuePathStruct


class XmlProcessor:

    __classifier: BinClassifier
    __config: Dict[str, str]
    __targets: List[(str, List[ValueNamePair])]
    __source_path: str
    __name_nodes: Set[str]
    __template_path: str

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
        # advertise instance as iterator for lists of value-name-pairs
        return self

    def build_template(self, source_path: str, template_path: str) -> None:
        """
        Creates a template file from the existing xml document by purging it from every node that exists more then once

        :param source_path: the path to the file to condense
        :param template_path: the path to the file where to write the result to
        """
        def remove_if_multiple_exist(node: ElemTree.Element) -> None:
            for sub_node in node:
                # first check the child nodes
                remove_if_multiple_exist(sub_node)
            needs_removal = self._has_same_name_children(node)
            if not needs_removal:
                return
            sub_nodes = list(node)
            # this will iterate over all child nodes except the first one in reverse order
            for i in range(len(sub_nodes) - 1, 0, -1):
                node.remove(sub_nodes[i])

        tree = ElemTree.parse(source_path)
        root = tree.getroot()
        for main_node in self._get_main_node_names():
            list_root = root.findall(".//{}".format(main_node))[0]
            remove_if_multiple_exist(list_root)
        self.__template_path = template_path
        dir_path = os.path.dirname(template_path)
        if dir_path:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        # tree.write(template_path)
        with open(template_path, "w") as file:
            print(self.__prettify(tree), file=file)

    def write_xml(self, path_to_file: str, template_path: str, path_pairs: List[List[PathCluster]]) -> int:
        # TODO: write some nice docu here
        def path_to_indexed(path_to_reduce: str) -> str:
            """
            Reduces the given path down to the element which is indexed in path
            """
            result = re.match(r"^.*?(?=\[i])", path_to_reduce)
            if not result:
                return ""
            return result.group()

        def path_of_parent(current_path: str) -> str:
            """
            Returns the path without the last node of the path
            """
            if current_path.endswith("/"):
                # cut away the last symbol as this breaks the expected behaviour from os
                current_path = current_path[:-1]
            # abuse the os package
            return os.path.dirname(current_path)

        def remove_first_two_nodes(path_to_reduce: str) -> str:
            """
            Removes the first 2 nodes of the given path and returns the rest of the path
            """
            # TODO: this seems like a very inefficient way -> find a better one
            result = re.match(r"^\w+/\w+/", path_to_reduce)
            if not result:
                raise AttributeError("Path '{}' is incorrect: expecting at least 2 nodes: list anchor & item".format(
                    path_to_reduce))
            return path_to_reduce[len(result.group()):]

        tree = ElemTree.parse(template_path)
        root = tree.getroot()
        insert_count = []
        for xml_classes in path_pairs:
            count = 0
            for entry in xml_classes:
                # use the first node as template -> create a working copy: modify it and append it to the existing nodes
                working_copy = copy.deepcopy(root.findall(".//{}".format(entry.base_path))[0])
                name_path = remove_first_two_nodes(entry.name_path)
                name_node: ElemTree.Element = working_copy.findall(".//{}".format(name_path))[0]
                name_node.text = entry.name
                # for path_struct in entry.value_path_pairs:
                #    current_path = remove_first_two_nodes(path_struct.path)
                # insert the copy
                current_root = root.findall(".//{}".format(path_of_parent(entry.base_path)))[0]
                current_root.append(working_copy)
                # remove the template
                if count == 0:
                    current_root.remove(current_root[0])
                count += 1
            insert_count.append(count)
        dir_path = os.path.dirname(template_path)
        if dir_path:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        with open(path_to_file, "w") as file:
            print(self.__prettify(tree), file=file)
        return sum(insert_count)

    def group_target_paths(self, unsorted_paths: List[str]) -> List[GeneratorStruct]:
        """
        Groups the given paths into classes in form of GeneratorStructs and assigns them these classes. The function
        assigns all paths or will crash trying

        :param unsorted_paths: the path to order
        :return: a list of xml-class structs
        """
        return GeneratorStruct.construct_from(self.__name_nodes, unsorted_paths)

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

    @staticmethod
    def __prettify(elem: ElemTree.ElementTree) -> str:
        """
        Corrects the indentation for the generated XML
        :param elem: the final tree to prettify
        :return: a string which has the well known XML-structure
        """
        # courtesy goes to https://pymotw.com/2/xml/etree/ElementTree/create.html#pretty-printing-xml
        # and https://stackoverflow.com/a/14493981
        tree_str = ElemTree.tostring(elem.getroot(), encoding='utf-8', method='xml')
        restructured = minidom.parseString(tree_str)
        # return restructured.toprettyxml(indent="  ", newl="")
        return '\n'.join([line for line in restructured.toprettyxml(indent="  ").split('\n') if line.strip()])



