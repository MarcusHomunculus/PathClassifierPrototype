from __future__ import annotations
from openpyxl.cell.cell import Cell

from matcher.internal.enum.CellPropertyType import CellPropertyType


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
