from enum import IntEnum
from typing import List, Tuple, Iterator


class CellMatchResult(IntEnum):
    NO_FINDING = 0
    ALL_FOUND = 1
    NAME_FOUND = 2
    VALUE_FOUND = 3


class CellMatchingStruct:
    success_type: CellMatchResult
    expected: str
    __expected: str
    __pool: List[Tuple[str, str]]

    def __init__(self, value_name_pairs: Iterator[Tuple[str, str]]):
        """
        The constructor

        :param value_name_pairs: A list of values pairs with there root node name
        """
        self.success_type = CellMatchResult.NO_FINDING
        self.__expected = ""
        self.__pool = list(value_name_pairs)

    def test_value(self, value: str) -> CellMatchResult:
        """
        Tests the given values against the values (and names) which are expected to be found

        :param value: the value to test against the list of value-name-pairs given to the constructor
        :return: if something could be matched in the form of an enum
        """
        if self.success_type is CellMatchResult.NO_FINDING:
            for entry in self.__pool:
                if entry[0] == value:
                    self.expected = entry[1]
                    self.success_type = CellMatchResult.VALUE_FOUND
                elif entry[1] == value:
                    self.expected = entry[0]
                    self.success_type = CellMatchResult.NAME_FOUND
                return self.success_type
        if self.success_type.value > 1:
            # means either the value or the name is missing
            if self.expected == value:
                self.success_type = CellMatchResult.ALL_FOUND
            return self.success_type
