import re


class PathOperator:

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
    def is_child_path_except_for(to_check: str, base_path: str) -> int:
        # TODO: doc me
        first_path = to_check.split("/")
        second_path = base_path.split("/")
        if len(first_path) > len(second_path):
            raise AttributeError("First argument should be a child path of the 2nd: {} vs {}".format(
                to_check, base_path))
        for i in range(len(first_path)):
            if i >= len(second_path):
                # only return the rest
                return len(first_path) - len(second_path)
            if first_path[i] != second_path[i]:
                return len(first_path) - i
        # then they are equal
        return 0

    @staticmethod
    def extract_attribute_name(to_extract_from: str) -> str:
        """
        Extracts the attributes name from the path given

        :param to_extract_from: the path leading to an attribute
        :return: the name of the attribute the path points to
        """
        success = re.search(r"(?<=@)\w+$", to_extract_from)
        if success:
            return success.group(1)
        return ""

    @staticmethod
    def is_attribute_path_of(to_check: str, node_path: str) -> bool:
        """
        Checks if both paths are equal except for that to_check addresses an attribute of node_path

        :param to_check: the path that potentially points to an attribute
        :param node_path: the path that potentially points to the node of the attribute in to_check
        :return: true if to_check addresses an attribute of node_path else false
        """
        to_check_is_node = PathOperator.is_nodes_only(to_check)
        node_path_is_node = PathOperator.is_nodes_only(node_path)
        if to_check_is_node or not node_path_is_node:
            return False
        attribute_name = PathOperator.extract_attribute_name(to_check)
        if not attribute_name:
            assert "Reached an invalid state: to_check should match on the attribute"
        if node_path not in to_check:
            # maybe there's a shortcut here
            return False
        # remove the trailing separator if the original doesn't have one
        extra_char = 0 if node_path.endswith('/') else 1
        # cut away the attribute: if then both are equal to_check is an attribute path of node_path
        reduced_path = to_check[:len(attribute_name) + extra_char + 1]      # +1 for the '@' in the attributes name
        if reduced_path == node_path:
            return True
        return False
