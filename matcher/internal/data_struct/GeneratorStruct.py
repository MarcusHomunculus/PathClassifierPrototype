from typing import List
import re


class GeneratorStruct:
    root_path: str
    name_path: str
    node_paths: List[str]

    def __init__(self, path_collection: List[str]):
        # TODO: write some docu here -> recommend not to use it
        # the structure is kinda standardized: the 1st node is the general group node, the 2nd is the root node for
        # every "thing" -> as all of them have to have them just pick the first
        self.__root_path = GeneratorStruct.extract_base_path(path_collection[0])

    @staticmethod
    def construct_from(path_collection: List[str]) -> List[str]:
        pass

    @staticmethod
    def get_node_count(node_path: str) -> int:
        """
        Counts the nodes the path addresses excluding the last attribute if present

        :param node_path: the path to count the node of
        :return: the count of actual nodes in the path
        """
        # as intermediate attributes and path changes are not to be expected
        path_parts = node_path.split("/")
        if path_parts[-1].startswith("@"):
            return len(path_parts) - 1
        return len(path_parts)

    @staticmethod
    def is_nodes_only(node_path: str) -> bool:
        """
        Returns if the node contains only nodes or if attributes are included

        :param node_path: the path to check
        :return: if the last path element is an attribute or not
        """
        # regex checks if a '@' is in front of the very last word
        return bool(re.match(r"@\w+$", node_path))

    @staticmethod
    def extract_base_path(to_extract_from) -> str:
        """
        Extracts the base path from the given path which is the first 2 nodes only

        :param to_extract_from: the path which holds the wanted information
        :return: the path of the 2 first nodes
        """
        try:
            # regex matches the first 2 words separated by a '/'
            return re.search(r"^\w+/\w+\b", to_extract_from).group(1)
        except AttributeError:
            raise AttributeError("Path seems to violate the path structure: {}".format(to_extract_from))
