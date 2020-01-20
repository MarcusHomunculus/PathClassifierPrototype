from typing import List, Tuple, Set

from matcher.path.PathOperations import PathOperator


class GeneratorStruct:

    root_path: str
    name_path: str
    node_paths: List[str]   # do not use a set here to ensure ordering

    def __init__(self, name_path: str):
        # TODO: write some docu here -> recommend not to use it
        # the structure is kinda standardized: the 1st node is the general group node, the 2nd is the root node for
        # every "thing" -> as all of them have to have them just pick the first
        self.root_path = PathOperator.extract_base_path(name_path)
        self.name_path = name_path
        self.node_paths = []

    def matches_jurisdiction(self, path_to_check: str) -> bool:
        """
        Checks if the given path falls into the base class / base path this instance represents

        :param path_to_check: the path to check for applicability to this instance
        :return: if the instance class and the path fall into the class or not
        """
        return self.root_path in path_to_check

    def add_path(self, to_add: str) -> bool:
        """
        Inserts the path given into the list of paths if it belongs to the structs base path

        :param to_add: the path to insert
        :return: true if the path had been added else false
        """
        if not self.matches_jurisdiction(to_add):
            return False
        index = self.__get_index_of_nearest_neighbor(to_add)
        if index == -1:
            # just append it
            index = len(self.node_paths)
        self.node_paths.insert(index, to_add)
        return True

    @staticmethod
    def construct_from(name_paths: Set[str], path_collection: List[str]) -> List[str]:
        # TODO: I need some docu here
        pass

    def __get_index_of_nearest_neighbor(self, to_find_neighbor_of) -> int:
        """
        Returns the index in which the given path should be inserted depending on the existing paths in the list.
        Recommendation depends on direct affiliation to an existing path (attribute path to its parenting node path and
        vice versa) and if the path is in the same scope of already existing paths. Scope is changed in this scenario
        when child nodes contain a list of the same node (which is indicated by the iteration symbol in the name).
        If no association can be made an invalid index is returned

        :param to_find_neighbor_of: the path to get an index for
        :return: the recommended index and -1 if no affiliation could be made
        """
        def find_next_non_attribute(index_start: int) -> int:
            """
            Returns the index of the path which does not address an attribute starting from the given index

            :param index_start: the index to start looking
            :return: the index of the first path addressing a node
            """
            for idx in range(start=index_start, stop=len(self.node_paths)):
                if PathOperator.is_nodes_only(self.node_paths[i]):
                    return i

        given_is_attribute_path = not PathOperator.is_nodes_only(to_find_neighbor_of)
        if given_is_attribute_path:
            def is_affiliated(x: str) -> bool: return PathOperator.is_attribute_path_of(to_find_neighbor_of, x)
        else:
            def is_affiliated(x: str) -> bool: return PathOperator.is_attribute_path_of(x, to_find_neighbor_of)
        for i in range(len(self.node_paths)):
            current_path = self.node_paths[i]
            if is_affiliated(current_path):
                return (i + 1) if given_is_attribute_path else (i - 1)
            if PathOperator.share_same_scope(current_path, to_find_neighbor_of):
                # as long they share the same scope it's fine -> just check that attributes stay with their parent
                return find_next_non_attribute(i + 1)
        # probably a different scope -> indicate this with an invalid index
        return -1
