from __future__ import annotations

from enum import Enum
from matcher.XlsxProcessor import XlsxProcessor


# Moved to dedicated file as using it as nested class made more trouble then it was worth it
class CellPropertyType(Enum):
    NONE = 0
    CONTENT = 1
    WIDTH = 2

    def __str__(self):
        if self.value == self.CONTENT:
            return XlsxProcessor.CELL_PROPERTY_CONTENT
        elif self.value == self.WIDTH:
            return XlsxProcessor.CELL_PROPERTY_WIDTH
        return ""

    @staticmethod
    def from_str(source_str: str) -> CellPropertyType:
        if source_str == XlsxProcessor.CELL_PROPERTY_CONTENT:
            return CellPropertyType.CONTENT
        elif source_str == XlsxProcessor.CELL_PROPERTY_WIDTH:
            return CellPropertyType.WIDTH
        return CellPropertyType.NONE
