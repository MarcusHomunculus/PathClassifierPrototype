from __future__ import annotations
from typing import List, Iterator, Tuple
from openpyxl.cell import Cell
from enum import Enum

from matcher.shared.ValueNamePair import ValueNamePair
from matcher.xlsx.location.CellPositioning import CellPosition


class CrossTableStruct:

    class FindingState(Enum):
        NO_FIND = 0
        NAME_FOUND = 1
        VALUE_FOUND = 2

    __opposite_value: str
    __opposite_list: List[str]
    __first_position_is_value: bool
    first_find: CellPosition
    opposite_find: CellPosition
    REQUIRED_SUCCESS_RATE = 0.5

    def __init__(self):
        """
        The constructor. The usage is discouraged in favor of the static function values_exist_in
        """
        self.__opposite_value = ""
        self.__opposite_list = []
        self.__first_position_is_value = False
        self.first_find = CellPosition.create_invalid()
        self.opposite_find = CellPosition.create_invalid()

    def find_other_pair_values_in(self, to_check: Iterator[Cell]) -> bool:
        """
        Checks if the given cell collection contains enough samples of from either the values list or the name list
        depending on what was found with the call of values_exist_in()

        :param to_check: the cell collection to check for the other part of the value-name-pair
        :return: true if enough values had been found
        """
        if not self.__opposite_list:
            return False
        work = list(self.__opposite_list)
        for cell in to_check:
            if cell.value in work:
                work.remove(cell.value)
                # housekeeping
                if cell.value == self.__opposite_value:
                    self.opposite_find = CellPosition.create_from(cell)
        if len(work) <= (1 - self.REQUIRED_SUCCESS_RATE) * len(self.__opposite_list):
            return True
        return False

    def contains_counterpart(self, to_check: Cell) -> bool:
        """
        Returns true if the given cell contains the expected value to match the first hit with the call to
        values_exist_in()

        :param to_check: the cell to check the value of
        :return: true if the value matches the expected value else false
        """
        return to_check.value == self.__opposite_value

    def get_sample_size(self) -> int:
        """
        Returns how many data points are used to detect a cross table

        :return: the count of value-name pairs
        """
        if not self.__opposite_list:
            return -1
        return len(self.__opposite_list)

    def is_complete(self) -> bool:
        """
        Returns if all required data for deriving the cross-tables structure has been set

        :return: true if the struct contains all required data else false
        """
        return self.first_find.is_valid() and self.opposite_find.is_valid()

    def first_position_represents_value(self):
        """
        Answers if the first position describes the location of a value

        :return: true if the position points to a value else it returns false which means it points to a name
        """
        return self.__first_position_is_value

    @staticmethod
    def values_exist_in(to_scan: Iterator[Cell], to_find: Iterator[ValueNamePair]) -> Tuple[bool, CrossTableStruct]:
        """
        Initializes the struct in a working state and returns it along with an indicator if continuing assuming a
        cross table with the expected data makes sense

        :param to_scan: the cell-line to check for the expected value-name pairs
        :param to_find: the expected data
        :return: a tuple if enough entries could be found and if so a struct which holds the required data to continue
        """
        values, names = ValueNamePair.unzip(to_find)
        # a set only allows unique entries -> finding the same value multiple time will therefor yield only one entry
        found_indices = set()
        read_state = CrossTableStruct.FindingState.NO_FIND
        result_container = CrossTableStruct()
        for cell in to_scan:
            if cell.value is None:
                continue
            for i in range(len(values)):
                if cell.value == values[i] and read_state == CrossTableStruct.FindingState.NO_FIND:
                    # this branch should only be reached once so set all struct members possible to set
                    result_container.__opposite_value = names[i]
                    result_container.__opposite_list = names
                    result_container.__first_position_is_value = True
                    result_container.first_find = CellPosition.create_from(cell)
                    found_indices.add(i)
                    read_state = CrossTableStruct.FindingState.VALUE_FOUND
                elif cell.value == values[i] and read_state == CrossTableStruct.FindingState.VALUE_FOUND:
                    # only do the book keeping
                    found_indices.add(i)
                elif cell.value == names[i] and read_state == CrossTableStruct.FindingState.NO_FIND:
                    result_container.__opposite_value = values[i]
                    result_container.__opposite_list = values
                    result_container.__first_position_is_value = False
                    result_container.first_find = CellPosition.create_from(cell)
                    found_indices.add(i)
                    read_state = CrossTableStruct.FindingState.NAME_FOUND
                elif cell.value == names[i] and read_state == CrossTableStruct.FindingState.NAME_FOUND:
                    found_indices.add(i)
        # perform the "post-processing"
        if not result_container.__opposite_value:
            # value has not been set -> so no data found -> abort and return an empty struct
            return False, CrossTableStruct()
        # check if there have been enough hits to call it a success
        if len(values) - len(found_indices) > len(values) * (1 - CrossTableStruct.REQUIRED_SUCCESS_RATE):
            return False, CrossTableStruct()
        return True, result_container
