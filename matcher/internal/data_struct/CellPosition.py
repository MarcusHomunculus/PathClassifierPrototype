from __future__ import annotations
from openpyxl.cell.cell import Cell

from matcher.internal.enum.CellPropertyType import CellPropertyType


class CellPosition:

    row: int
    col: str
    read_type: CellPropertyType

    def __init__(self, row: int, column: str, cell_property: CellPropertyType):
        # TODO: doc me
        self.row = row
        self.col = column
        self.read_type = cell_property

    def is_valid(self) -> bool:
        # TODO: write some nice docu here
        return self.row > 0 and self.col and self.read_type != CellPropertyType.NONE

    @staticmethod
    def create_from(cell: Cell, cell_property: CellPropertyType) -> CellPosition:
        # TODO: your docu could stand right here
        return CellPosition(cell.row, cell.row, cell_property)

    @staticmethod
    def create_invalid() -> CellPosition:
        # TODO: I need some docu here
        return CellPosition(-1, "", CellPropertyType.NONE)
