from enum import IntEnum
from typing import List, Iterator

from matcher.internal.data_struct.ValueNamePair import ValueNamePair


class CellMatchResult(IntEnum):
    # please keep in mind that this enum is interpreted via a bitmask
    NO_FINDING = 0
    ALL_FOUND = 1
    NAME_FOUND = 2
    VALUE_FOUND = 3


class CellMatchingStruct:
    success_type: CellMatchResult
    __expected: str
    __pool: List[ValueNamePair]

    def __init__(self, value_name_pairs: Iterator[ValueNamePair], skip_validation: bool = False):
        """
        The constructor

        :param value_name_pairs: A list of values pairs with there root node name
        :param skip_validation: set this flag if the test for the constructors data shall be disabled
        """
        self.success_type = CellMatchResult.NO_FINDING
        self.__expected = ""
        self.__pool = list(value_name_pairs)
        if skip_validation:
            return
        if len(self.__pool) < 1:
            raise AttributeError("Can't be initialized with an empty list")

    def test_value(self, value: str) -> CellMatchResult:
        """
        Tests the given values against the values (and names) which are expected to be found

        :param value: the value to test against the list of value-name-pairs given to the constructor
        :return: if something could be matched in the form of an enum
        """
        if self.success_type is CellMatchResult.NO_FINDING:
            for entry in self.__pool:
                to_return = CellMatchResult.NO_FINDING
                # check if the value is **in** the value rather then for equality for higher flexibility
                # -> if types can be distinguished (by extracting them from eg. the XML-Schema) it would make more sense
                # to check numerical values vor equality or double values for a certain count of digits
                if entry.value in value:
                    self.__expected = entry.value
                    to_return = self.success_type = CellMatchResult.VALUE_FOUND
                elif entry.name in value:
                    self.__expected = entry.name
                    to_return = self.success_type = CellMatchResult.NAME_FOUND
                return to_return
        if self.success_type.value > 1:
            # means either the value or the name is missing
            if self.__expected in value:
                self.success_type = CellMatchResult.ALL_FOUND
                return self.success_type
            return CellMatchResult.NO_FINDING
        return CellMatchResult.NO_FINDING

    def get_value_name_pairs(self) -> List[ValueNamePair]:
        """
        Returns a copy of the stored value-name pairs

        :return: a list of tuple which represent value-name pairs
        """
        return list(self.__pool)

    def get_missing_entry(self) -> str:
        """
        If a name (or value) has been found the other part of the pair can be received with this call. If no pair has
        been selected in the list of value-name-pairs an empty string is returned

        :return: the companion entry to an already found name (or value) or an empty string
        """
        return self.__expected
