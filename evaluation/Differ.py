import logging
import xml.etree.ElementTree as ElemTree
from typing import Dict, Tuple, List

from creation.FileSystem import create_directories_for


class XmlDiffer:

    __sink: logging.Logger
    __log_path: str

    def __init__(self, log_path: str):
        # TODO: write some nice docu here
        create_directories_for(log_path)
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

    def compare(self, first_file: str, second_file) -> None:
        # TODO: I need some docu here
        print("Starting comparision of {} with {}. Writing results to {}".format(first_file, second_file,
                                                                                 self.__log_path))
        tree_1 = ElemTree.parse(first_file)
        tree_2 = ElemTree.parse(second_file)
        root_1 = tree_1.getroot()
        root_2 = tree_2.getroot()
        start_path = root_1.tag
        self._process_node(root_1, root_2, start_path, first_file, second_file)

    def _process_node(self, to_process_1: ElemTree.Element, to_process_2: ElemTree.Element, current_path: str,
                      first_name: str, second_name: str) -> None:
        # TODO: doc me!
        def compare_attributes(attributes_1: Dict[str, str], attributes_2: Dict[str, str], node_path: str) -> None:
            """
            Compares the attribute dictionaries from the 2 nodes and checks for mismatches and missing entries

            :param attributes_1: the attributes from the node of the first file
            :param attributes_2: the attributes from the node of the second file
            :param node_path: the node path to the attributes
            """
            missing_attribute_template = "Missing attribute {} in file {} under {}"
            keys_read = []
            for key in attributes_1.keys():
                if key not in attributes_2:
                    self.__sink.error(missing_attribute_template.format(key, second_name, node_path))
                    continue
                # keep track of the keys read from node 1 to compare it to the list of keys from node 2
                # -> find unprocessed ones of node 2
                keys_read.append(key)
                if attributes_1[key] != attributes_2[key]:
                    self.__sink.error("Mismatch in attribute values for {} under {}. {}: {} vs {}: {}".format(key,
                                      node_path, first_name, attributes_1[key], second_name, attributes_2[key]))
                    continue
            keys_2 = list(attributes_2.keys())
            for key in keys_read:
                if key in keys_2:
                    keys_2.remove(key)
            # all leftovers have to be reported as they are extra in the second node
            for key in keys_2:
                self.__sink.error(missing_attribute_template.format(key, first_name, node_path))

        def process_different_types(node_1: ElemTree.Element, node_2: ElemTree.Element) -> None:
            """
            Compares the 2 given nodes children if both nodes have children which carry all different names

            :param node_1: the first trees node
            :param node_2: the second trees node
            """
            processed_nodes = []
            for child in node_1:
                new_path = "{}/{}".format(current_path, child.tag)
                # find the counterpart
                other = node_2.find(child.tag)
                if other is None:
                    self.__sink.error("Missing node {} in {}".format(new_path, second_name))
                processed_nodes.append(child.tag)
                self._process_node(child, other, new_path, first_name, second_name)
            # check the nodes from file 2 which might have been missed
            tags = list(map(lambda x: x.tag, list(node_2)))
            for tag in processed_nodes:
                if tag in tags:
                    tags.remove(tag)
            # report the leftovers
            for tag_name in tags:
                self.__sink.error("Missing node {}/{} in {}".format(current_path, tag_name, first_name))

        def calculate_error_distance(reference_node: ElemTree.Element, distance_to: ElemTree.Element) -> int:
            # TODO: write some awesome docu here
            def zero_or_greater(to_eval: int) -> int:
                # TODO: I short doc string would help here a lot
                return to_eval if to_eval > 0 else 0

            distance = 0
            if reference_node.text.strip() != distance_to.text.strip():
                distance += 1
            for key in reference_node.attrib.keys():
                if key not in distance_to.attrib:
                    distance += 1
                    continue
                if reference_node.attrib[key] != distance_to.attrib[key]:
                    distance_to += 1
            distance += zero_or_greater(len(reference_node.attrib) - len(distance_to.attrib))
            return distance

        def process_same_types(node_1: ElemTree.Element, node_2: ElemTree.Element) -> None:
            """
            Tries to match nodes with another (when all child-nodes of the given one have children with the same name)
            in order to compare them properly

            :param node_1: the first trees node
            :param node_2: the second trees node
            """
            def find_match_in_node_2(to_find: int) -> Tuple[bool, ElemTree.Element]:
                """
                Goes through the children of the 2nd node given and returns the one that matches. If none could be
                found False and a dummy node is returned

                :param to_find: the hash of the node to find in the 2nd nodes children
                :return: true and the node in case of success else false and a dummy node
                """
                for child_tmp in node_2:
                    if self.__create_hash(child_tmp) == to_find:
                        return True, child_tmp
                return False, node_2[0]

            def find_alternative(given: ElemTree.Element, blacklist: List[int]) -> Tuple[bool, ElemTree.Element]:
                """
                Goes through the list of child nodes of the second node and returns the one with the lowest error
                distance that haven't been processed yet

                :param given: the node of which the alternative shall be found
                :param blacklist: the list of node hashes that have already been processed
                :return: true and the match in case of a low error distance else false and a dummy node
                """
                min_distance = -1
                min_child = node_2[0]
                for candidate in node_2:
                    if self.__create_hash(candidate) in blacklist:
                        continue
                    distance = calculate_error_distance(given, candidate)
                    if distance >= min_distance > 0:
                        continue
                    min_distance = distance
                    min_child = candidate
                if min_distance > 0:
                    return True, min_child
                return False, min_child

            # all nodes have the same tag name so just pick the first as template
            new_path = "{}/{}".format(current_path, node_1[0].tag)
            processed_hashes_1 = []     # this list holds the consumed children from node 1
            processed_hashes_2 = []     # this list holds the consumed children from node 2
            for list_child in node_1:
                child_hash = self.__create_hash(list_child)
                success, other = find_match_in_node_2(child_hash)
                if success:
                    self._process_node(list_child, other, new_path, first_name, second_name)
                    processed_hashes_1.append(child_hash)
                    processed_hashes_2.append(child_hash)
                    continue
                # find an alternative
                success, alternative = find_alternative(list_child, processed_hashes_2)
                if success:
                    self._process_node(list_child, alternative, new_path, first_name, second_name)
                    processed_hashes_1.append(child_hash)
                    processed_hashes_2.append(self.__create_hash(alternative))
                    continue
                # this means the list children from node 2 is exhausted -> break here and continue with the error
                # reporting
                break
            result_1 = len(list(node_1)) - len(processed_hashes_1)
            if result_1 > 0:
                self.__sink.error("Have {} leftover node(s) under {} in {}".format(result_1, current_path, first_name))
            result_2 = len(list(node_2)) - len(processed_hashes_2)
            if result_2 > 0:
                self.__sink.error("Have {} leftover node(s) under {} in {}".format(result_2, current_path, second_name))
            pass

        def contains_value(to_test: ElemTree.Element) -> bool:
            """
            Returns if the given node contains an actual value or not
            """
            return not to_test.text.isspace()

        if contains_value(to_process_1) or contains_value(to_process_2):
            # if either one of them is not empty
            if contains_value(to_process_1) and contains_value(to_process_2):
                if to_process_1.text != to_process_2.text:
                    self.__sink.error("Mismatch in values of {}. {}: {} vs. {}: {}".format(current_path, first_name,
                                      to_process_1.text, second_name, to_process_2.text))
            else:
                self.__sink.error("Missing value in node {} in {}".format(current_path,
                                  second_name if contains_value(to_process_1) else second_name))
        if to_process_1.attrib or to_process_2.attrib:
            # compare the attributes
            if to_process_1.attrib and to_process_2.attrib:
                compare_attributes(to_process_1.attrib, to_process_2.attrib, current_path)
            else:
                self.__sink.error("Missing attributes for node {} in file {}".format(current_path,
                                  second_name if to_process_1.attrib else first_name))
        # check if children exist at all
        if not to_process_1 or not to_process_2:
            if not to_process_1 and not to_process_2:
                return  # no children exist
            if not to_process_1:
                self.__collect_missing_children(to_process_2, first_name)
                return
            if not to_process_2:
                self.__collect_missing_children(to_process_1, second_name)
                return
        # with children existing check if it is a list of nodes with the all-the-same-name or not
        needs_indexing = self.__has_item_list(to_process_1)
        if needs_indexing:
            # sort them, compare them and be done with them
            process_same_types(to_process_1, to_process_2)
        else:
            # just go deeper the rabbit hole -> update the path
            process_different_types(to_process_1, to_process_2)

    def __collect_missing_children(self, other_node, source_name: str) -> None:
        pass

    @staticmethod
    def __create_hash(to_hash: ElemTree.Element) -> int:
        """
        Creates a hash representation of the elements name (tag), its value and its attributes

        :param to_hash: the element to create a hash of
        :return: the hash calculated
        """
        element_hash = hash(to_hash.tag)
        # treat eventual whitespaces equal
        element_hash += hash(to_hash.text) if not to_hash.text.isspace() else 0
        # inspired by https://stackoverflow.com/a/1151705
        element_hash += 0 if not to_hash.attrib else hash(tuple(sorted(to_hash.attrib.items())))
        return element_hash

    @staticmethod
    def __has_item_list(to_check: ElemTree.Element) -> bool:
        """
        Checks the tags of the child nodes and returns if it contains mixed names or if all names carry the same
        name

        :param to_check: the node to check the children of
        :return: true if all child-nodes are of the same type else false
        """
        start_name = ""
        for child in to_check:
            if start_name == "":
                start_name = child.tag
                continue
            elif child.tag != start_name:
                # assume that all have different tag names or all tags are the same
                return False
        return True
