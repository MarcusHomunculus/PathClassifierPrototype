from __future__ import annotations
from openpyxl.cell.cell import Cell
from enum import IntEnum

from matcher.internal.enum.CellPropertyType import CellPropertyType
from matcher.internal.data_struct.CellMatching import CellMatchingStruct


class CellPositionStructType(IntEnum):
    NO_FINDING = 0
    HEADER_FOUND = 1
    DATA_FOUND = 2


class CellPosition:

    row: int
    column: str
    read_type: CellPropertyType

    def __init__(self, row: int, column: str, cell_property: CellPropertyType):
        """
        The constructor

        :param row: the row index of the cell as xlsx counts them
        :param column: the column letter of the cell
        :param cell_property: the property of the cell to read to receive the data it addresses
        """
        self.row = row
        self.column = column
        self.read_type = cell_property

    def is_valid(self) -> bool:
        """
        Returns if the instance is representing sane data
        """
        return self.row > 0 and self.column and self.read_type != CellPropertyType.NONE

    @staticmethod
    def create_from(cell: Cell, cell_property: CellPropertyType) -> CellPosition:
        """
        A factory method to create an instance from a openpyxl.Cell instance

        :param cell: the cell to take the "coordinates" from
        :param cell_property: the property to get the content the instance is addressing
        :return: an instance of CellPosition
        """
        return CellPosition(cell.row, cell.row, cell_property)

    @staticmethod
    def create_invalid() -> CellPosition:
        """
        Creates a dummy instance of CellPosition which holds useless information
        :return: an instance of CellPosition with data which can't be encountered in xlsx-files
        """
        return CellPosition(-1, "", CellPropertyType.NONE)


class CellPositionStruct:
    read_result: CellPositionStructType
    match_struct: CellMatchingStruct
    value_position: CellPosition
    name_or_forward_position: CellPosition
    value_path: str

    def __init__(self,
                 read_result: CellPositionStructType,
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
    def create_no_find() -> CellPositionStruct:
        """
        Creates an empty instance which represents the information that nothing of use could be found

        :return an instance representing nothing
        """
        return CellPositionStruct(CellPositionStructType.NO_FINDING, CellMatchingStruct([]), CellPosition.create_invalid(),
                                  CellPosition.create_invalid(), "")

    @staticmethod
    def create_header_found(forward_position: CellPosition) -> CellPositionStruct:
        """
        Creates an instance which represents that a header was detected and at which position the forwarding content
        could be matched

        :param forward_position: the position of the forwarding column or row
        :return: an instance representing a header (which in itself) is only of importance for were to start reading
        """
        # instantiate an empty matching struct with no list -> use the name member to transport the forward index
        return CellPositionStruct(CellPositionStructType.HEADER_FOUND, CellMatchingStruct([]), CellPosition.create_invalid(),
                                  forward_position, "")

    @staticmethod
    def create_data_pair_found(match_result: CellMatchingStruct,
                               value_position: CellPosition,
                               name_position: CellPosition) -> CellPositionStruct:
        """
        Creates an instance which holds the position of the data found

        :param match_result: the struct holding the match information
        :param value_position: the position of the value in the table
        :param name_position: the position of the name in the table
        :return: an instance representing an success in finding a value name pair in the given line
        """
        return CellPositionStruct(CellPositionStructType.DATA_FOUND, match_result, value_position, name_position, "")

    @staticmethod
    def create_value_found(match_result: CellMatchingStruct,
                           value_position: CellPosition,
                           value_path: str) -> CellPositionStruct:
        """
        Creates an instance which holds the state when only a value has been found

        :param match_result: the struct holding the match information
        :param value_position: the position of the value in the table
        :param value_path: in case of the search was forwarded to another file set this param to indicate the final path
        :return: an instance representing in success finding a value but not more
        """
        return CellPositionStruct(CellPositionStructType.DATA_FOUND, match_result, value_position, CellPosition.create_invalid(),
                                  value_path)

    def contains_header_forwarding_position(self) -> bool:
        """
        Answers if the struct represents a header which holds a valid position for a header row or column

        :return: true if its an instance of a header which has forwarding information
        """
        return self.read_result == CellPositionStructType.HEADER_FOUND and self.name_or_forward_position.is_valid()

    def contains_value_forwarding_path(self) -> bool:
        """
        Returns if the value path is set or not. If so the value path and the name path should differ in the path
        information given to the classifier

        :return: true if the value has been set in case of forwarding else false
        """
        return bool(self.value_path)
