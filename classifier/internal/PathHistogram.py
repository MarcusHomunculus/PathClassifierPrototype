from typing import List, Tuple
import logging

from classifier.error.MatchExceptions import NoMatchCandidateException


class PathHistogram:

    __source_path: str
    __matched_paths: List[str]
    __match_bins: List[int]

    def __init__(self, key: str):
        """
        The constructor

        :param key: the source path the instance represents and the sink file path should be collected for
        """
        self.__source_path = key
        self.__matched_paths = []
        self.__match_bins = []
        self.__last_match = ""

    def add_matched_path(self, possible_match_path: str) -> None:
        """
        Allows to increase the count for the path given

        :param possible_match_path: the path to the value which matches the given one
        """
        def match_index(to_find: str) -> int:
            """
            Goes through the list of stored paths and returns -1 if the path does
            not exist yet. In contrast the list.index() function would raise an
            ValueError which is not wanted
            :param to_find: the path to find the index of
            :return: the index if the path could be found else -1
            """
            for i in range(len(self.__matched_paths)):
                if self.__matched_paths[i] == to_find:
                    return i
            return -1

        idx = match_index(possible_match_path)
        if idx == -1:
            self.__matched_paths.append(possible_match_path)
            idx = len(self.__matched_paths) - 1
        if len(self.__match_bins) <= idx:
            self.__match_bins.append(0)
        self.__match_bins[idx] += 1

    def get_highest_match(self) -> (str, bool):
        """
        Returns the path with the highest match count and if the match count is unique within the container. If this is
        not true the clustering can be assumed to have failed

        :return: the path with the highest match count and if this count was unique
        """
        max_val_is_unique = True
        max_val = -1
        max_idx = 0
        if not self.__match_bins:
            logging.error(NoMatchCandidateException("Could not match path '{}' to any path in the sink file".format(
                self.get_key())))
            return "", False
        for i in range(len(self.__match_bins)):
            if self.__match_bins[i] > max_val:
                max_val = self.__match_bins[i]
                max_idx = i
                max_val_is_unique = True
            elif self.__match_bins[i] == max_val:
                # uniqueness is not given right now
                max_val_is_unique = False
        return self.__matched_paths[max_idx], max_val_is_unique

    def get_key(self) -> str:
        """
        Returns the key which the possible path matches relate to

        :return: the path of the source value
        """
        return self.__source_path

    def to_tuple(self) -> Tuple[str, List[Tuple[str, int]]]:
        """
        Flattens the collection to a tuple with the source path and a list of tuples with the sink file paths and their
        count

        :return: a tuple of a string and a list of string-integer-tuples
        """
        if len(self.__match_bins) != len(self.__matched_paths):
            raise AssertionError("Having different length for paths and bins: {} vs {}".format(
                len(self.__matched_paths), len(self.__match_bins)))
        bin_data: List[Tuple[str, int]] = list(zip(self.__matched_paths, self.__match_bins))
        return self.get_key(), bin_data
