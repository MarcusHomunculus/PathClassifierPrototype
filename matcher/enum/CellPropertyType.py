from __future__ import annotations

from enum import Enum

from matcher.immutability.Constant import Constant


# Moved to dedicated file as using it as nested class made more trouble then it was worth it
class CellPropertyType(Enum):
    NONE = 0
    CONTENT = 1
    WIDTH = 2

    CELL_PROPERTY_CONTENT = Constant("c")
    CELL_PROPERTY_WIDTH = Constant("w")

    def __str__(self):
        if self.value == 1:
            return self.CELL_PROPERTY_CONTENT
        elif self.value == 2:
            return self.CELL_PROPERTY_WIDTH
        # raise ValueError("Unsupported type")
        return ""

    @staticmethod
    def from_str(source_str: str) -> CellPropertyType:
        if source_str == CellPropertyType.CELL_PROPERTY_CONTENT:
            return CellPropertyType.CONTENT
        elif source_str == CellPropertyType.CELL_PROPERTY_WIDTH:
            return CellPropertyType.WIDTH
        return CellPropertyType.NONE
