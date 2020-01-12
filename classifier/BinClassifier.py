from typing import List, Dict
from classifier.internal.BinCollection import BinCollection
from classifier.error.MatchExceptions import MultipleMatchingCandidatesException


class BinClassifier:

    __mat: List[BinCollection]
    __last_source: str
    __result_buffer: Dict[str, str]

    def __init__(self):
        """
        The constructor
        """
        self.__mat = []
        self.__last_source = ""
        self.__result_buffer = {}

    def add_source_path(self, source: str) -> None:
        """
        Allows to set a path which all following potential matches will be assigned to. Except a new path is specified
        via add_source_path or add_potential_match

        :param source: the path to the data in the source file
        """
        # first check if the path already exists -> this is a real scenario for the team-nodes in the sections: it makes
        # more sense to just add these to the existing data rather then skipping them in the reading process as in the
        # best case they reassure the data
        for collection in self.__mat:
            if collection.get_key() == source:
                self.__last_source = source
                return
        # else it is a new path
        self.__mat.append(BinCollection(source))
        self.__last_source = source

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
