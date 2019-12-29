from __future__ import annotations
from typing import List, Tuple, Iterator, Dict
import re
from openpyxl import load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet

from matcher.internal.CellPropertyType import CellPropertyType
from classifier.BinClassifier import BinClassifier


class XlsxProcessor:

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

    class PathDataCluster:
        value_id: str
        value_property: CellPropertyType
        name_id: str
        name_property: CellPropertyType

        def __init__(self, value_id: str,
                     value_property: CellPropertyType,
                     name_id: str,
                     name_property: CellPropertyType):
            """
            The constructor for a cluster holding data to build a path
            :param value_id: the volatile identifier part of the cell for the value cell
            :param value_property: the property the value was derived from
            :param name_id: the volatile identifier part of the cell for the name cell
            :param name_property: the property the name was derived from
            """
            self.value_id = value_id
            self.value_property = value_property
            self.name_id = name_id
            self.name_property = name_property

    FORWARDING_KEY = "forwarding_on"
    TEMPLATE_CELL_ADDRESS_ROW_WISE = "${}{}:{}"
    TEMPLATE_CELL_ADDRESS_COL_WISE = "{}${}:{}"

    __classifier: BinClassifier
    __config = {}
    __root_xlsx: str
    __nested_xlsx_dir: str

    def __init__(self,
                 sink: BinClassifier,
                 config: Dict[str, str],
                 path_root_xlsx: str,
                 nested_xlsx_dir: str = "nested/"):
        """
        The constructor

        :param sink: the classifier to push the matches into
        :param config: a dictionary constructed from the config file
        :param path_root_xlsx: the path to the main Excel file
        :param nested_xlsx_dir: the path to the other Excel files which the root file might reference to
        """
        self.__classifier = sink
        self.__config = config
        self.__root_xlsx = path_root_xlsx
        root_file_name = re.search(r"\b\w*\.xlsx$", path_root_xlsx).group(0)
        root_path = path_root_xlsx[:-len(root_file_name)]
        if not nested_xlsx_dir.endswith("/"):
            nested_xlsx_dir += "/"
        self.__nested_xlsx_dir = root_path + nested_xlsx_dir

    def match_given_values_in(self, value_name_pairs: Iterator[Tuple[str, str]]) -> None:
        """
        Manages itself through the given xlsx-file and and tries to match the given pairs in the files (somewhere)

        :param value_name_pairs: a list of tuples with values and their corresponding URI
        """
        wb = load_workbook(self.__root_xlsx, True)
        sheet_names = wb.sheetnames
        for sheet in sheet_names:
            self.__search_sheet_for_values(value_name_pairs, wb[sheet], self.__root_xlsx)

    def __search_sheet_for_values(self, value_name_pairs: Iterator[Tuple[str, str]], sheet: Worksheet, path: str):
        """
        Analyses the given sheet in the way that it tries to find the given value-URI-pairs in all constellations it
        knows by just applying all and throw the result at the classifier

        :param value_name_pairs: a list of tuples with values and their corresponding URI
        :param sheet: the sheet to go through
        :param path: the current path to the sheet (for the classifier)
        """
        # usually a table is build column wise: so go through the sheet row wise to have a hit on the value and the
        # name
        self.__check_row_wise(sheet, value_name_pairs, path)
        # on good luck try it column wise
        # self.__check_column_wise(sheet, value_name_pairs, path)
        # self.__check_as_cross_table(sheet, value_name_pairs, path)

    def __check_row_wise(self, sheet: Worksheet, value_name_pairs: Iterator[Tuple[str, str]], path: str) -> None:
        """
        Iterates through the rows of the sheet given and tries to match the given list of value-URI-pairs in a row-wise
        fashion. If a match could be made the resulting path is pushed into the classifier

        :param sheet: the sheet to search for matches
        :param value_name_pairs: the stuff (hopefully) to find in the sheet given
        :param path: the path to the current sheet (excluding the sheet itself)
        """
        lowest_header_row: int = 0
        header_color = self.__config["header_{}".format(sheet.title)]
        for values in sheet.iter_rows():
            val: Cell
            first_result: XlsxProcessor.CellMatchStruct = XlsxProcessor.CellMatchStruct(False)
            for val in values:
                # skip empty cells
                if val.value is None:
                    continue
                # housekeeping for the final path
                if val.fill.bgColor.rgb == header_color and val.row >= lowest_header_row:
                    lowest_header_row = val.row
                    # the header is not of interest in a row-wise table as the classifier ignores header names
                    continue
                if not first_result.success:
                    first_result = self.__match_cell_properties_to(val, value_name_pairs)
                    if not first_result.success:
                        continue
                # in the team file the cell holds the name and its size determines the size property -> so check this
                # one against the expected value, too
                if first_result.success:
                    second_result = self.__match_expected_in(val, first_result, False)
                    if not second_result[0]:
                        continue
                    # assemble the path for the classifier it can match later on
                    row_data_start = lowest_header_row + 1
                    value_cell = self.__to_linear_cell_address(False, second_result[1].value_id, row_data_start,
                                                               second_result[1].value_property)
                    name_cell = self.__to_linear_cell_address(False, second_result[1].name_id, row_data_start,
                                                              second_result[1].name_property)
                    final_path = "{}/{}/@{};{}".format(path, sheet.title, value_cell, name_cell)
                    # self.__classifier.add_potential_match(final_path)
                    # there shouldn't be anymore data in this row
                    break
        return

    @staticmethod
    def __match_cell_properties_to(to_read: Cell, value_name_pairs: Iterator[Tuple[str, str]]) -> CellMatchStruct:
        """
        Extracts all supported properties of a cell (including its content) and checks if one property can be matched
        to the list of value name pairs given. This function ignores the property of the cell matched on because it
        is assumed that the first match will be on the identifier which should be the content of the cell anyway

        :param to_read: the cell to check the properties of
        :param value_name_pairs: a list of values expected
        :return: a struct containing data for further processing
        """
        for to_find in value_name_pairs:
            props = XlsxProcessor.__extract_cell_properties(to_read)
            for prop in props.keys():
                if prop == to_find[0]:
                    # return that the value has been found
                    return XlsxProcessor.CellMatchStruct(True, to_find[1], to_read, False, props[prop])
                elif prop == to_find[1]:
                    # allowing identifiers outside of the content of cells makes no sense -> if this is the case crash
                    if props[prop] != CellPropertyType.CONTENT:
                        raise ValueError("Can't allow an identifier that is encoded in the cell except for its content")
                    # return that the name has been found
                    return XlsxProcessor.CellMatchStruct(True, to_find[0], to_read, True, CellPropertyType.CONTENT)
        # means nothing has been found: return an invalid struct
        return XlsxProcessor.CellMatchStruct(False)

    @staticmethod
    def __match_expected_in(to_read: Cell, previous_data: CellMatchStruct, return_rows: bool)\
            -> Tuple[bool, XlsxProcessor.PathDataCluster]:
        """
        Checks the given cell if it contains the data expected

        :param to_read: the cell to check for the expected content / value
        :param previous_data: the data which was collected with the first match
        :param return_rows: if the 2nd and the 3rd tuple members should contain the rows or column letters of the
                            matched cells
        :return: a tuple which tells if a match could be made and if so contains the cell ID where the value and the
                 cell ID where the name was matched (the ID depends on the 3rd function parameter)

        """
        def assemble_success_data(property_type: CellPropertyType) -> Tuple[bool, XlsxProcessor.PathDataCluster]:
            """
            Builds the tuple to return by using the data available in the outer function

            :return: the final result of the matching with the path data when a match was successful
            """
            first_id = previous_data.found_one.row if return_rows else previous_data.found_one.column_letter
            second_id = to_read.row if return_rows else to_read.column_letter
            if previous_data.found_one_is_name:
                name_id = first_id
                if previous_data.found_ones_property_indicator != CellPropertyType.CONTENT:
                    # allowing to derive IDs from other cell properties then their content is a pitfall -> abort then
                    raise AttributeError
                name_property = CellPropertyType.CONTENT
                value_id = second_id
                value_property = property_type
            else:
                name_id = second_id
                if property_type != CellPropertyType.CONTENT:
                    # allowing to derive IDs from other cell properties then their content is a pitfall -> abort then
                    raise AttributeError
                name_property = CellPropertyType.CONTENT
                value_id = first_id
                value_property = previous_data.found_ones_property_indicator
            return True, XlsxProcessor.PathDataCluster(value_id, value_property, name_id, name_property)

        props = XlsxProcessor.__extract_cell_properties(to_read)
        for prop in props.keys():
            if prop == previous_data.expected:
                return assemble_success_data(props[prop])
        return False, XlsxProcessor.PathDataCluster("", CellPropertyType.NONE, "", CellPropertyType.NONE)

    @staticmethod
    def __extract_cell_properties(to_extract_from: Cell) -> Dict[str, CellPropertyType]:
        """
        Takes the cell an creates a list of properties from it

        :param to_extract_from: the cell the properties are wanted from
        :return: a list of all properties supported
        """
        return {str(to_extract_from.value): CellPropertyType.CONTENT}

    @staticmethod
    def __to_linear_cell_address(is_fixed_row: bool, col: str, row: int, property_identifier: CellPropertyType) -> str:
        """
        Inserts the given arguments into the template given. This function is merely a reminder to use a template

        :param is_fixed_row: if the template should assume a row-wise reading scheme or a column-wise scheme
        :param col: the column to insert
        :param row: the row to insert
        :param property_identifier: the identifier of the cell property to use as source
        :return: a properly formatted string to be used as cell address
        """
        if is_fixed_row:
            template = XlsxProcessor.TEMPLATE_CELL_ADDRESS_COL_WISE
        else:
            template = XlsxProcessor.TEMPLATE_CELL_ADDRESS_ROW_WISE
        return template.format(col, row, str(property_identifier))
