from typing import List, Dict, Tuple

from classifier.internal.BinCollection import BinCollection
from classifier.error.MatchExceptions import MultipleMatchingCandidatesException


class BinClassifier:

    __mat: List[BinCollection]
    __last_source: str
    __result_buffer: Dict[str, str]

    def __init__(self):
        self.__mat = []
        self.__last_source = ""
        self.__result_buffer = {}

    def add_source_path(self, source: str) -> None:
        """
        Allows to set a path which all following potential matches will be assigned to. Except a new path is specified
        via add_source_path or add_potential_match

        :param source: the path to the data in the source file
        """
        self.__mat.append(BinCollection(source))
        self.__last_source = source

    def get_active_source_path(self):
        """
        Returns the path under which current matches would be added with add_potential_match() if no source path would
        be given

        :return: the active source file path
        """
        return self.__last_source

    def add_potential_match(self, match_path: str, source_path: str = "") -> None:
        """
        Allows to add a new sink path to an either already added source path or the source path specified

        :param match_path: the path to a potential match in the sink file
        :param source_path: the path to data in the source file
        """
        if source_path == "":
            source_path = self.__last_source
        if source_path == "" or match_path == "":
            raise ValueError("Can't operate with empty strings")
        for entry in self.__mat:
            if entry.get_key() == source_path:
                entry.add_matched_path(match_path)

    def train(self) -> None:
        """
        Performs the learning / matching based on the data received previously
        """
        for path_bin in self.__mat:
            path, success = path_bin.get_highest_match()
            if not success:
                raise MultipleMatchingCandidatesException("Found matches with same count for path {}".format(
                    path_bin.get_key()))
            self.__result_buffer[path] = path_bin.get_key()

    def dump_raw_data(self) -> List[Tuple[str, List[Tuple[str, int]]]]:
        """
        Dumps the classifiers matrix as a list of rows

        :return: a list of tuples containing a string and a list of string-integer-pairs
        """
        tuple_list = map(lambda x: x.to_tuple(), self.__mat)
        return list(tuple_list)
