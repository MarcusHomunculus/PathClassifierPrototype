from __future__ import annotations
from enum import IntEnum

from matcher.internal.data_struct.CellMatching import CellMatchingStruct
from matcher.internal.data_struct.CellPosition import CellPosition


class LineResultType(IntEnum):
    NO_FINDING = 0
    HEADER_FOUND = 1
    DATA_PAIR_FOUND = 2
    VALUE_FOUND = 3


class LineResultStruct:
    read_result: LineResultType
    match_struct: CellMatchingStruct
    value_position: CellPosition
    name_or_forward_position: CellPosition
    value_path: str

    def __init__(self,
                 read_result: LineResultType,
                 data_result: CellMatchingStruct,
                 value_position: CellPosition,
                 name_position: CellPosition,
                 value_path: str):
        """
        The constructor which is discouraged to be used outside of the static factory methods
        """
        self.read_result = read_result
        self.match_struct = data_result
        self.value_position = value_position
        self.name_or_forward_position = name_position
        self.value_path = value_path

    @staticmethod
    def create_no_find() -> LineResultStruct:
        """
        Creates an empty instance which represents the information that nothing of use could be found

        :return an instance representing nothing
        """
        return LineResultStruct(LineResultType.NO_FINDING, CellMatchingStruct([]), CellPosition.create_invalid(),
                                CellPosition.create_invalid(), "")

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
                                forward_position, "")

    @staticmethod
    def create_data_pair_found(match_result: CellMatchingStruct,
                               value_position: CellPosition,
                               name_position: CellPosition) -> LineResultStruct:
        """
        Creates an instance which holds the position of the data found

        :param match_result: the struct holding the match information
        :param value_position: the position of the value in the table
        :param name_position: the position of the name in the table
        :return: an instance representing an success in finding a value name pair in the given line
        """
        return LineResultStruct(LineResultType.DATA_PAIR_FOUND, match_result, value_position, name_position, "")

    @staticmethod
    def create_value_found(match_result: CellMatchingStruct,
                           value_position: CellPosition,
                           value_path: str) -> LineResultStruct:
        """
        Creates an instance which holds the state when only a value has been found

        :param match_result: the struct holding the match information
        :param value_position: the position of the value in the table
        :param value_path: in case of the search was forwarded to another file set this param to indicate the final path
        :return: an instance representing in success finding a value but not more
        """
        return LineResultStruct(LineResultType.VALUE_FOUND, match_result, value_position, CellPosition.create_invalid(),
                                value_path)

    def header_contains_forwarding(self) -> bool:
        """
        Answers if the struct represents a header which holds a valid position for a header row or column

        :return: true if its an instance of a header which has forwarding information
        """
        return self.read_result == LineResultType.HEADER_FOUND and self.name_or_forward_position.is_valid()

    def contains_forwarding_path(self) -> bool:
        """
        Returns if the value path is set or not. If so the value path and the name path should differ in the path
        information given to the classifier

        :return: true if the value has been set in case of forwarding else false
        """
        return bool(self.value_path)
