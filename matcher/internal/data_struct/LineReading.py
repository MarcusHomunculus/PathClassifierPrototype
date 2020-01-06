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
        """
        Creates an empty instance which represents the information that nothing of use could be found

        :return an instance representing nothing
        """
        return LineResultStruct(LineResultType.NO_FINDING, CellMatchingStruct([]), CellPosition.create_invalid(),
                                CellPosition.create_invalid())

    @staticmethod
    def create_header_found(forward_position: CellPosition) -> LineResultStruct:
        """
        Creates an instance which represents that a header was detected and at which position the forwarding content
        could be matched

        :param forward_position: the position of the forwarding column or row
        :return: an instance representing a header (which in itself) is only of importance for were to start reading
        """
        # instantiate an empty matching struct with no list -> use the name member to transport the forward index
        return LineResultStruct(LineResultType.HEADER_FOUND, CellMatchingStruct([]), CellPosition.create_invalid(),
                                forward_position)

    @staticmethod
    def create_data_found(match_result: CellMatchingStruct,
                          value_position: CellPosition,
                          name_position: CellPosition) -> LineResultStruct:
        """
        Creates an instance which holds the position of the data found

        :param match_result: the struct holding the match information
        :param value_position: the position of the value in the table
        :param name_position: the position of the name in the table
        :return: an instance representing an success in finding a value name pair in the given line
        """
        return LineResultStruct(LineResultType.DATA_FOUND, match_result, value_position, name_position)

    def contains_forwarding(self) -> bool:
        """
        Answers if the struct represents a header which holds a valid position for a header row or column

        :return: true if its an instance of a header which has forwarding information
        """
        return self.read_result == LineResultType.HEADER_FOUND and self.name_or_forward_position.is_valid()
