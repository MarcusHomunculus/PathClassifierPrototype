from typing import List
from enum import Enum, auto


class SourceReader:
    """
    This class reads in the data from the excel source and makes it available
    in a queryable interface
    """

    class ValueType(Enum):
        """
        Represents the different data type labels
        """
        VALUE_ONLY = auto()
        COLUMN_VAL = auto()
        ROW_VAL = auto()
        CELL_DATA = auto()
        CROSS_VAL_POS = auto()
        CROSS_VAL_NEG = auto()

    __paths: List[str]

    def __init__(self, paths: List[str]):
        self.__paths = paths.copy()

    def train(self):
        """
        Learns the structure of the excel source in contrast to the target format
        :return:
        """
        pass

    def __get_devices(self) -> List[List[str]]:
        """
        This function uses clustering to find all devices. This requires for the
        devices to appear in all excel files.
        :return: a list of all hits with additional data as the **potential** column
        header and row header
        """
        pass

    def __train_for_classify_type(self, data_tuples: List[List[str]]) -> List[ValueType]:
        """
        This function retrieves the labels to the data tuples and trains a classifier
        with it
        :param data_tuples: the data from the cluster algorithm
        :return: the list of according labels matching in index the data tuples
        """
        pass

