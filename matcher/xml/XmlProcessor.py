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
from matcher.path.FileSystem import create_directories_for


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
        create_directories_for(template_path)
        # tree.write(template_path)
        with open(template_path, "w") as file:
            print(self.__prettify(tree), file=file)

    def write_xml(self, target_file: str, template_path: str, path_pairs: List[List[PathCluster]]) -> int:
        """
        Writes the received data into the specified file by using the file under template_path as blue-print

        :param target_file: the path under which the result is to store
        :param template_path: the path to the template file
        :param path_pairs: the data to fill the template with
        :return: the number of nodes inserted into the final file
        """
        def contains_index(to_check: str) -> bool:
            """
            Returns if the index identifier can be found in the given string
            """
            return "[i]" in to_check

        tree = ElemTree.parse(template_path)
        root = tree.getroot()
        insert_count = []
        for xml_classes in path_pairs:
            count = 0
            # all entries represent the same type so just pick the first
            node_template = self.__copy_template_and_delete(root, xml_classes[0].base_path)
            for entry in xml_classes:
                # use the first node as template -> create a working copy: modify it and append it to the existing nodes
                working_copy = copy.deepcopy(node_template)
                name_node = self.__first_node_of(working_copy, self.__remove_first_two_nodes(entry.name_path))
                name_node.text = entry.name
                for path_struct in entry.value_path_pairs:
                    if contains_index(path_struct.path):
                        self.__set_values_on(working_copy, path_struct)
                    else:
                        self.__set_depending_on_path(working_copy, path_struct.path, path_struct.values[0])
                # insert the copy
                current_root = self.__first_node_of(root, self.__path_of_parent(entry.base_path))
                current_root.append(working_copy)
                count += 1
            insert_count.append(count)
        create_directories_for(target_file)
        with open(target_file, "w") as file:
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

    @staticmethod
    def __first_node_of(search_anchor: ElemTree.Element, relative_path: str) -> ElemTree.Element:
        """
        Returns the first node that can be found under the given path in the given node

        :param search_anchor: the node to search for the wanted path
        :param relative_path: the path to the desired node from the anchor on
        :return: the first element that could be found
        """
        # if there's no node to find there's no reason to start looking
        if not relative_path:
            return search_anchor
        return search_anchor.findall(".//{}".format(relative_path))[0]

    @staticmethod
    def __remove_first_two_nodes(path_to_reduce: str) -> str:
        """
        Removes the first 2 nodes of the given path and returns the rest of the path
        """
        # TODO: this seems like a very inefficient way -> find a better one
        result = re.match(r"^\w+/\w+/", path_to_reduce)
        if not result:
            raise AttributeError("Path '{}' is incorrect: expecting at least 2 nodes: list anchor & item".format(
                path_to_reduce))
        return path_to_reduce[len(result.group()):]

    @staticmethod
    def __set_depending_on_path(working_node: ElemTree.Element, path: str, value: str,
                                remove_first_nodes: bool = True) -> None:
        """
        Sets the value on the given path in the node depending on the path as value or attribute

        :param working_node: the node to search for the path
        :param path: the path which describes where to set the value in the working_node
        :param value: the value to set to
        """
        def split_on_attribute(to_split: str) -> Tuple[str, str]:
            """
            Splits the given path if it addresses an attribute and returns the node path and the attribute name as
            tuple
            """
            # path can have only one anyway
            parts = to_split.split("@")
            if len(parts) != 2:
                raise AttributeError("Cant split '{}' into its path and its attribute".format(to_split))
            return (parts[0])[:-1], parts[1]  # remove the trailing '/' in the path

        if not path:
            # the node itself is addressed
            working_node.text = value
            return
        if path.startswith("@"):
            # only set the attribute on the the node itself
            attribute_name = path[1:]
            working_node.attrib[attribute_name] = value
            return
        # else it is a longer path
        if remove_first_nodes:
            path = XmlProcessor.__remove_first_two_nodes(path)

        if not XmlProcessor.__is_attribute_path(path):
            # easy: just set the value and be done with it
            to_set = XmlProcessor.__first_node_of(working_node, path)
            to_set.text = value
            return
        node_path, node_attribute = split_on_attribute(path)
        to_set = XmlProcessor.__first_node_of(working_node, node_path)
        to_set.attrib[node_attribute] = value

    @staticmethod
    def __path_of_parent(path_to_reduce: str) -> str:
        """
        Returns the path without the last node of the path

        :param path_to_reduce: the path which should be reduced for the last node
        :return: the path without the last node
        """
        if path_to_reduce.endswith("/"):
            # cut away the last symbol as this breaks the expected behaviour from os
            path_to_reduce = path_to_reduce[:-1]
        # abuse the os package
        return os.path.dirname(path_to_reduce)

    @staticmethod
    def __copy_template_and_delete(base_node: ElemTree.Element, node_path: str) -> ElemTree.Element:
        """
        Creates a deep copy of the node under the specified path and deletes the original while returning the copy

        :param base_node: the path from which the node path is valid
        :param node_path: the path of the node to copy
        :return: a deep copy of the node under the path
        """
        template = XmlProcessor.__first_node_of(base_node, node_path)
        to_return = copy.deepcopy(template)
        # remove the template
        parent = XmlProcessor.__first_node_of(base_node, XmlProcessor.__path_of_parent(node_path))
        parent.remove(template)
        return to_return

    @staticmethod
    def __set_values_on(main_node: ElemTree.Element, generator: ValuePathStruct) -> None:
        """
        If multiple values have to be set on indexed nodes this function will take of it

        :param main_node: the node which hosts the indexed nodes
        :param generator: the container holding the indexed path(s) and their values
        """
        def split_on_index(path_to_split: str) -> Tuple[str, str]:
            """
            Splits the given path at the (single!!) index identifier and returns the resulting paths left and right of
            the identifier

            :param path_to_split: the path to separate
            :return: a tuple of the 2 resulting paths
            """
            parts = path_to_split.split("[i]")
            if len(parts) != 2:
                raise AttributeError("Could not split '{}' on the index identifier".format(path_to_split))
            if not parts[1]:
                # means no path after the index
                return parts[0], ""
            return parts[0], (parts[1])[1:]

        if XmlProcessor.__is_attribute_path(generator.path):
            # the higher instance ensures that values come before attributes -> all nodes already exist
            # XPath starts counting with 1
            generator.adapt_offset_to(1)
            for pair in generator:
                value, path = pair
                XmlProcessor.__set_depending_on_path(main_node, XmlProcessor.__remove_first_two_nodes(path), value,
                                                     False)
            return
        node_path, inner_node_path = split_on_index(generator.path)
        collect_node = XmlProcessor.__first_node_of(main_node, XmlProcessor.__path_of_parent(
            XmlProcessor.__remove_first_two_nodes(node_path)))
        template = XmlProcessor.__copy_template_and_delete(main_node, XmlProcessor.__remove_first_two_nodes(node_path))
        for pair in generator:
            working_copy = copy.deepcopy(template)
            value, _ = pair
            XmlProcessor.__set_depending_on_path(working_copy, inner_node_path, value, False)
            collect_node.append(working_copy)

    @staticmethod
    def __is_attribute_path(to_test: str) -> bool:
        """
        Returns if the path at hand addresses an attribute or not
        """
        return "@" in to_test
