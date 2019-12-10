from typing import List
from classifier.internal.BinCollection import _BinCollection


class BinClassifier:

    __mat: List[_BinCollection]
    __last_source: str

    def __init__(self):
        self.__mat = []
        self.__last_source = ""

    def add_source_path(self, source: str):
        # TODO: your docu could stand right here
        self.__mat.append(_BinCollection(source))
        self.__last_source = source

    def add_potential_match(self, match_path: str, source_path: str = ""):
        # TODO: write some docu here
        if source_path == "":
            source_path = self.__last_source
        if source_path == "" or match_path == "":
            raise ValueError("Can't operate with empty strings")
        for entry in self.__mat:
            if entry.get_key() == source_path:
                entry.add_matched_path(match_path)

    def train(self):
        pass
