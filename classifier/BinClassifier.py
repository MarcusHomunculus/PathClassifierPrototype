from typing import List, Dict, Tuple
import logging

from classifier.internal.PathHistogram import PathHistogram
from classifier.error.MatchExceptions import MultipleMatchingCandidatesException


class BinClassifier:

    __mat: List[PathHistogram]
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
        self.__mat.append(PathHistogram(source))
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
        for path_histogram in self.__mat:
            path, success = path_histogram.get_highest_match()
            if not success:
                logging.error(MultipleMatchingCandidatesException("Found matches with same count for path {}".format(
                    path_histogram.get_key())))
            # store in reverse order as the idea is to have a translation from the sink to the source -> source shall be
            # generated
            self.__result_buffer[path] = path_histogram.get_key()

    def get_final_sink_paths(self) -> List[str]:
        """
        Returns the list of selected sink paths from the training step

        :return: all sink paths which were selected for their source path matching
        """
        return list(self.__result_buffer.keys())

    def get(self, sink_path: str, return_empty_if_no_match: bool = False) -> str:
        """
        Allows to receive the source path to the matched sink path in a dictionary-like fashion.

        :param sink_path: the path for which the source path is wanted for
        :param return_empty_if_no_match: set this flag if an empty string shall be returned instead of an KeyError
        :return: the source path to the given sink path (if it was selected as match for it)
        """
        result = self.__result_buffer.get(sink_path)
        if result is not None:
            return result
        if result is None and return_empty_if_no_match:
            return ""
        raise KeyError("Path '{}' is not registered with classifier".format(sink_path))

    def dump_raw_data(self) -> List[Tuple[str, List[Tuple[str, int]]]]:
        """
        Dumps the classifiers matrix as a list of rows

        :return: a list of tuples containing a string and a list of string-integer-pairs
        """
        tuple_list = map(lambda x: x.to_tuple(), self.__mat)
        return list(tuple_list)
