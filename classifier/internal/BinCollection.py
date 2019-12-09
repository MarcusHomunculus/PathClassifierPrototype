from typing import List
import operator


class _BinCollection:

    __source_path: str
    __matched_paths: List[str]
    __match_bins: List[int]

    def __init__(self, source_path: str):
        self.__source_path = source_path
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
        if len(self.__match_bins) < idx:
            self.__match_bins.append(0)
        self.__match_bins[idx] += 1

    def get_highest_match(self) -> (str, bool):
        """
        Returns the path with the highest match count and if the match count is unique within the container. If this is
        not true the matching can be assumed to have failed

        :return: the path with the highest match count and if this count was unique
        """
        max_val_is_unique = True
        max_val = -1
        max_idx = 0
        for i in range(len(self.__match_bins)):
            if self.__match_bins[i] > max_val:
                max_val = self.__match_bins[i]
                max_idx = i
                max_val_is_unique = True
            elif self.__match_bins[i] == max_val:
                # uniqueness is not given right now
                max_val_is_unique = False
        return self.__matched_paths[max_idx], max_val_is_unique
