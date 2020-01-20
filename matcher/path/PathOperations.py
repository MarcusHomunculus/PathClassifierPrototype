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
            return re.match(r"^\w+/\w+\b", to_extract_from).group()
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
    def share_same_scope(to_check: str, to_check_against: str) -> bool:
        # TODO: doc me -> mention that an index starts a new scope
        def is_new_scope(path_element: str) -> bool:
            # TODO: write some nice docu here
            return path_element.endswith("[i]")

        first_path = to_check.split("/")
        second_path = to_check_against.split("/")
        max_len = len(first_path) if len(first_path) > len(second_path) else len(second_path)
        for i in range(max_len):
            if i >= len(first_path) and is_new_scope(second_path[i]):
                return False
            elif i >= len(second_path) and is_new_scope(first_path[i]):
                return False
            elif i >= len(second_path) or i >= len(first_path):
                continue
            # from here on i is within range of both lists lengths
            if first_path[i] == second_path[i]:
                continue
            elif is_new_scope(first_path[i]):
                return False    # only one starts a new scope -> both have different paths
            elif is_new_scope(second_path[i]):
                return False
        # no situation encountered where one enters a new scope -> might even be equal
        return True

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

    @staticmethod
    def contains_iterations(to_check: str) -> int:
        """
        Returns how many iteration appear in the given path
        :param to_check: the path to analyze
        :return: the count of iterator indicators
        """
        return to_check.count("[i]")
