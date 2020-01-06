from __future__ import annotations
from enum import IntEnum

from matcher.internal.data_struct.CellMatching import CellMatchingStruct
from matcher.internal.data_struct.CellPosition import CellPosition


class LineResultType(IntEnum):
    NO_FINDING = 0
    HEADER_FOUND = 1
    DATA_FOUND = 2


class LineResultStruct:
    read_result: LineResultType
    match_struct: CellMatchingStruct
    value_position: CellPosition
    name_or_forward_position: CellPosition

    def __init__(self,
                 read_result: LineResultType,
                 data_result: CellMatchingStruct,
                 value_position: CellPosition,
                 name_position: CellPosition):
        """
        The constructor which is discouraged to be used outside of the static factory methods
        """
        self.read_result = read_result
        self.match_struct = data_result
        self.value_position = value_position
        self.name_or_forward_position = name_position

    @staticmethod
    def create_no_find() -> LineResultStruct:
        # TODO: doc me
        return LineResultStruct(LineResultType.NO_FINDING, CellMatchingStruct([]), CellPosition.create_invalid(),
                                CellPosition.create_invalid())

    @staticmethod
    def create_header_found(forward_position: CellPosition) -> LineResultStruct:
        # TODO: write some expressive docu here
        # instantiate an empty matching struct with no list -> use the name member to transport the forward index
        return LineResultStruct(LineResultType.HEADER_FOUND, CellMatchingStruct([]), CellPosition.create_invalid(),
                                forward_position)

    @staticmethod
    def create_data_found(match_result: CellMatchingStruct,
                          value_position: CellPosition,
                          name_position: CellPosition) -> LineResultStruct:
        # TODO: I need some docu here
        return LineResultStruct(LineResultType.DATA_FOUND, match_result, value_position, name_position)
