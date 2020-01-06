from enum import Enum
from typing import List, Tuple, Iterator

from matcher.internal.data_struct.CellPosition import CellPosition


class CellMatchResult(Enum):
    NO_FINDING = 0
    NAME_FOUND = 1
    VALUE_FOUND = 2
    ALL_FOUND = 3


class CellMatchStruct:
    success_type: CellMatchResult
    expected: str
    position_name: CellPosition
    position_value: CellPosition
    __expected: str
    __pool: Iterator[Tuple[str, str]]

    def __init__(self, value_name_pairs: Iterator[Tuple[str, str]]):
        """
        The constructor

        :param value_name_pairs: A list of values pairs with there root node name
        """
        self.success_type = CellMatchResult.NO_FINDING
        self.__expected = ""
        self.position_name = CellPosition.create_invalid()
        self.position_value = CellPosition.create_invalid()
        self.__pool = value_name_pairs
