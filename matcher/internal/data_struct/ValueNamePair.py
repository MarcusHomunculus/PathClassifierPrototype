from __future__ import annotations
from typing import Iterator, List, Tuple


class ValueNamePair:
    name: str
    value: str

    def __init__(self, name: str, value: str):
        """
        Basic constructor

        :param name: the name associated to the data point
        :param value: the data point to find
        """
        self.name = name
        self.value = value

    @staticmethod
    def create_with_value(value: str) -> ValueNamePair:
        """
        Creates a "pair" only holding the data point

        :param value: the value to find
        :return: an instance of ValueNamePair with an empty name and the given value
        """
        return ValueNamePair("", value)

    @staticmethod
    def from_tuple(value_name_pair: Tuple[str, str]) -> ValueNamePair:
        """
        Creates a value name pair from a tuple of 2 strings

        :param value_name_pair: the value and its associated name in the form of a tuple
        :return: the tuple transformed to a pair
        """
        return ValueNamePair(value_name_pair[0], value_name_pair[1])

    @staticmethod
    def zip(values: Iterator[str], names: Iterator[str]) -> List[ValueNamePair]:
        """
        Transforms the list of names and values to a list of value-name-pairs

        :param values: the list of values
        :param names: the list of associated names in the same order as the values they belong to
        :return: all entries paired as given
        """
        to_return = []
        for v, n in zip(values, names):
            to_return.append(ValueNamePair(v, n))
        return to_return

    @staticmethod
    def unzip(to_separate: Iterator[ValueNamePair]) -> Tuple[List[str], List[str]]:
        """
        Separates the list of pairs into a tuple of lists for the values and the names

        :param to_separate: the list of value name pairs to break up
        :return: a tuple holding the list of values and the list of names
        """
        names = []
        values = []
        for pair in to_separate:
            names.append(pair.name)
            values.append(pair.value)
        return values, names
