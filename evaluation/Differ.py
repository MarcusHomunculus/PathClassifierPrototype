import logging
import xml.etree.ElementTree as ElemTree
import toml
from typing import Dict

from creation.ConfigDict import config_from_file


class XmlDiffer:

    __sink: logging.Logger
    __log_path: str

    def __init__(self, log_path: str):
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

    def _process_node(self, to_process_1: ElemTree.Element, to_process_2: ElemTree.Element, current_path: str,
                      first_name: str, second_name: str) -> None:
        # TODO: doc me!
        def has_item_list(to_check: ElemTree.Element) -> bool:
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

        def create_hash(to_hash: ElemTree.Element) -> int:
            """
            Creates a hash representation of the elements name (tag), its value and its attributes

            :param to_hash: the element to create a hash of
            :return: the hash calculated
            """
            element_hash = hash(to_hash.tag)
            # treat eventual whitespaces equal
            element_hash += hash(to_hash.text) if not to_hash.text.isspace() else 0
            element_hash += 0 if not to_hash.attrib else hash(to_hash.attrib)
            return element_hash

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

        if not to_process_1.text.isspace() or not to_process_2.text.isspace():
            # if either one of them is not empty
            pass
        if to_process_1.attrib or to_process_2.attrib:
            # compare the attributes
            if to_process_1.attrib and to_process_2.attrib:
                compare_attributes(to_process_1.attrib, to_process_2.attrib, current_path)
            elif to_process_1.attrib:
                self.__sink.error("Missing attributes for node {} in file {}".format(current_path, second_name))
            else:
                self.__sink.error("Missing attributes for node {} in file {}".format(current_path, first_name))
        # check if it is a list of nodes with the same name or not
        needs_indexing = has_item_list(to_process_1)
        if needs_indexing:
            # TODO: find a way to compare them anyway -> update the path
            # -> create a hash of the nodes and sort by the hash
            pass
        else:
            # just go deeper the rabbit hole -> update the path
            processed_nodes = []
            for child in to_process_1:
                new_path = "{}/{}".format(current_path, child.tag)
                # find the counterpart
                other = to_process_2.find(child.tag)
                if other is None:
                    self.__sink.error("Missing node {} in {}".format(new_path, second_name))
                processed_nodes.append(child.tag)
                self._process_node(child, other, new_path, first_name, second_name)
            # check the nodes from file 2 which might have been missed
            tags = map(lambda x: x.tag, to_process_2.iter())
            for tag in processed_nodes:
                if tag in tags:
                    processed_nodes.remove(tag)
            # report the leftovers
            for tag_name in tags:
                self.__sink.error("Missing node {}/{} in {}".format(current_path, tag_name, first_name))
