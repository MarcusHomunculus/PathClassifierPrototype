from __future__ import annotations
from typing import List, Iterator, Tuple
from openpyxl.cell import Cell
from enum import Enum

from matcher.internal.data_struct.ValueNamePair import ValueNamePair
from matcher.internal.data_struct.CellPositioning import CellPosition


class CrossTableStruct:

    class FindingState(Enum):
        NO_FIND = 0
        NAME_FOUND = 1
        VALUE_FOUND = 2

    __opposite_value: str
    __opposite_list: List[str]
    first_find: CellPosition
    opposite_find: CellPosition
    REQUIRED_SUCCESS_RATE = 0.5

    def __init__(self):
        """
        The constructor. The usage is discouraged in favor of the static function values_exist_in
        """
        self.__opposite_value = ""
        self.__opposite_list = []
        self.first_find = CellPosition.create_invalid()
        self.opposite_find = CellPosition.create_invalid()

    def found_other_values(self, to_check: Iterator[Cell]) -> bool:
        if not self.__opposite_list:
            return False
        # TODO: continue here

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
        found_indexes = set()
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
                    result_container.first_find = CellPosition.create_from(cell)
                    found_indexes.add(i)
                    read_state = CrossTableStruct.FindingState.VALUE_FOUND
                elif cell.value == values[i] and read_state == CrossTableStruct.FindingState.VALUE_FOUND:
                    # only do the book keeping
                    found_indexes.add(i)
                elif cell.value == names[i] and read_state == CrossTableStruct.FindingState.NO_FIND:
                    result_container.__opposite_value = values[i]
                    result_container.__opposite_list = values
                    result_container.first_find = CellPosition.create_from(cell)
                    found_indexes.add(i)
                    read_state = CrossTableStruct.FindingState.NAME_FOUND
                elif cell.value == names[i] and read_state == CrossTableStruct.FindingState.NAME_FOUND:
                    found_indexes.add(i)
        # perform the "post-processing"
        if not result_container.__opposite_value:
            # value has not been set -> so no data found -> abort and return an empty struct
            return False, CrossTableStruct()
        # check if there have been enough hits to call it a success
        if len(values) - len(found_indexes) > len(values) * (1 - CrossTableStruct.REQUIRED_SUCCESS_RATE):
            return False, CrossTableStruct()
        return True, result_container

