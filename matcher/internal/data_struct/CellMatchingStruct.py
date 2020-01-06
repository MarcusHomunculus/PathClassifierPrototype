from enum import Enum


class CellMatchResult(Enum):
    NO_FINDING = 0
    NAME_FOUND = 1
    VALUE_FOUND = 2
    ALL_FOUND = 3


class CellMatchStruct:
    success: bool
    expected: str
    found_one: Cell
    found_one_is_name: bool
    found_ones_property_indicator: CellPropertyType

    def __init__(self,
                 success: bool,
                 expected: str = "",
                 found_one: Cell = None,
                 found_name: bool = False,
                 property_type: CellPropertyType = CellPropertyType.NONE):
        """
        The constructor

        :param success: if the search for a value or name yielded a hit
        :param expected: the value or name to be found to match it to the content found
        :param found_one: the value that has triggered the success
        :param found_name: true if the content found was the name else the value has been found
        :param property_type: in case the value to the names has been found set this to indicate the property it was
                              derived from
        """
        # start with a sanity check
        if success and expected == "":
            raise ValueError("Received an empty expected value were a string must be")
        self.success = success
        self.expected = expected
        self.found_one = found_one
        self.found_one_is_name = found_name
        self.found_ones_property_indicator = property_type