from typing import List
from classifier.internal.BinCollection import _BinCollection


class BinClassifier:

    __mat: List[_BinCollection]
    __last_source: str

    def __init__(self):
        self.__mat = []
        self.__last_source = None

    def add_source_path(self, source: str):
        self.__mat.append(_BinCollection(source))
        self.__last_source = source
