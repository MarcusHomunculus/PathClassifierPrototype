from __future__ import annotations
from typing import List, Set, Tuple

from matcher.path.PathOperations import PathOperator


class GeneratorStruct:

    root_path: str
    name_path: str
    node_paths: List[str]   # do not use a set here to ensure ordering

    def __init__(self, name_path: str):
        """
        The constructor for one struct which is a container for a particular class (ie. root node) in the source file
        and their associated paths. It is recommended to use the function construct_from for instantiation

        :param name_path: the path to the name of the class in the source file
        """
        # the structure is kinda standardized: the 1st node is the general group node, the 2nd is the root node for
        # every "thing" -> as all of them have to have them just pick the first
        self.root_path = PathOperator.extract_base_path(name_path)
        self.name_path = name_path
        self.node_paths = []

    def __str__(self):
        return self.root_path

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
    def construct_from(name_paths: Set[str], path_collection: List[str]) -> List[GeneratorStruct]:
        """
        Builds a list of GeneratorStructs from the given name paths and distributes all paths in the collection among
        them. If a path can't be assigned a AttributeError is raised

        :param name_paths: the paths to the names in the source file
        :param path_collection: the source paths to the data in the file
        :return: a list of structs associated to their class in the source file and holding their ordered paths
        """
        struct_list: List[GeneratorStruct] = []
        for path in name_paths:
            struct_list.append(GeneratorStruct(path))
        # after the foundation has been laid continue with sorting the data paths
        # TODO: transform path_collection to a set to ensure uniqueness?
        for path in path_collection:
            success = False
            for struct in struct_list:
                success = struct.add_path(path)
                if success:
                    break
            if not success:
                raise AttributeError("Received a path that could not be associated with a base path: {}".format(path))
        return struct_list

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
            for idx in range(index_start, len(self.node_paths)):
                if PathOperator.is_nodes_only(self.node_paths[idx]):
                    return idx
            return len(self.node_paths)

        if not self.node_paths:
            # no neighbors to check so just return 0 to add it at the beginning
            return 0
        given_is_attribute_path = not PathOperator.is_nodes_only(to_find_neighbor_of)
        if given_is_attribute_path:
            def is_affiliated(x: str) -> bool: return PathOperator.is_attribute_path_of(to_find_neighbor_of, x)
        else:
            def is_affiliated(x: str) -> bool: return PathOperator.is_attribute_path_of(x, to_find_neighbor_of)
        for i in range(len(self.node_paths)):
            current_path = self.node_paths[i]
            if is_affiliated(current_path):
                return (i + 1) if given_is_attribute_path else i
        # separate these to ensure that nodes and their attribute paths always stay together
        for i in range(len(self.node_paths)):
            current_path = self.node_paths[i]
            if PathOperator.share_same_scope(current_path, to_find_neighbor_of):
                # as long they share the same scope it's fine -> just check that attributes stay with their parent
                return find_next_non_attribute(i + 1)
        # probably a different scope -> indicate this with an invalid index
        return -1


class ValuePathStruct:

    name: str
    values: List[str]
    path: str
    __offset: int
    __index_identifier = "[i]"
    __run: int

    def __init__(self, name: str, values: List[str], source_path: str, offset: int = 0):
        """
        The constructor

        :param name: the name to represent
        :param values: a list of values (usually this should be a list of one)
        :param source_path: the path to represent and cluster with the value
        :param offset: an optional parameter to influence the indexing for the path (if applicable)
        """
        self.name = name
        self.values = list(values)
        self.path = source_path
        self.__offset = offset
        self.__run = 0

    def __str__(self):
        return self.path

    def __iter__(self):
        return self

    def __next__(self) -> Tuple[str, str]:
        def replace_index(old_path: str, index: int) -> str:
            """
            Replaces the placeholder for the index with an index to the one given
            """
            # only replace one to ensure it fails later if multiple exist
            return old_path.replace(self.__index_identifier, "[{}]".format(index), 1)

        if self.__run >= len(self.values):
            raise StopIteration()
        self.__run += 1
        if self.__index_identifier not in self.path or len(self.values) < 2:
            return self.values[0], self.path
        else:
            return self.values[self.__run - 1], replace_index(self.path, self.__run + self.__offset - 1)


class PathCluster:

    name: str
    name_path: str
    base_path: str
    value_path_pairs: List[ValuePathStruct]

    def __init__(self, name: str, name_path: str, base_path: str):
        # TODO: doc me
        self.name = name
        self.name_path = name_path
        self.base_path = base_path
        self.value_path_pairs = []

    def add_pair(self, to_add: ValuePathStruct) -> None:
        # TODO: your docu could stand right here
        self.value_path_pairs.append(to_add)
