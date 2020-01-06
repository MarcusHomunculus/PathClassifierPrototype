from __future__ import annotations
from typing import List, Tuple, Iterator, Dict
import re
import os
from openpyxl import load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.utils import get_column_letter

from matcher.internal.enum.CellPropertyType import CellPropertyType
from matcher.internal.data_struct.CellMatching import CellMatchResult, CellMatchingStruct
from matcher.internal.data_struct.CellPosition import CellPosition
from classifier.BinClassifier import BinClassifier
from classifier.error.MatchExceptions import NoMatchCandidateException


class XlsxProcessor:

    # class CellLineResult:
    #     result: CellMatchingStruct
    #     position_value: CellPosition
    #     position_name: CellPosition
    #
    #     def __init__(self, result: CellMatchingStruct, position_value: CellPosition, position_name: CellPosition):
    #         """
    #         The constructor
    #
    #         :param result: the search result holding struct
    #         :param position_value: the cell position of the value found (might be invalid depending on the result)
    #         :param position_name: the cell position of the name found (might be invalid depending on the result)
    #         """
    #         self.result = result
    #         self.position_value = position_value
    #         self.position_name = position_name
    #
    #     def read_successful(self) -> bool:
    #         """
    #         Returns if a value-name-pair could be matched
    #         """
    #         return self.result == CellMatchResult.ALL_FOUND

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
        wb = load_workbook(self.__root_xlsx)
        sheet_names = wb.sheetnames
        for sheet in sheet_names:
            self._search_sheet_for_values(value_name_pairs, wb[sheet], self.__root_xlsx)

    def _search_sheet_for_values(self, value_name_pairs: Iterator[Tuple[str, str]], sheet: Worksheet, path: str):
        """
        Analyses the given sheet in the way that it tries to find the given value-URI-pairs in all constellations it
        knows by just applying all and throw the result at the classifier

        :param value_name_pairs: a list of tuples with values and their corresponding URI
        :param sheet: the sheet to go through
        :param path: the current path to the sheet (for the classifier)
        """
        self._check_row_wise(sheet, value_name_pairs, path)
        self._check_column_wise(sheet, value_name_pairs, path)
        self._check_as_cross_table(sheet, value_name_pairs, path)

    def _check_row_wise(self, sheet: Worksheet, value_name_pairs: Iterator[Tuple[str, str]], path: str) -> None:
        """
        Iterates through the rows of the sheet given and tries to match the given list of value-URI-pairs in a row-wise
        fashion. If a match could be made the resulting path is pushed into the classifier

        :param sheet: the sheet to search for matches
        :param value_name_pairs: the stuff (hopefully) to find in the sheet given
        :param path: the path to the current sheet (excluding the sheet itself)
        """
        # TODO: if forwarding becomes more complex maybe switch to a state machine?
        lowest_header_row: int = 0
        forward_idx = -1
        handle_forwarding, forwarding_column_name = self.__includes_forwarding(sheet.title)
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
                    # generally the header is not of interest in a row-wise table as the classifier ignores header names
                    # but check for forwarding
                    if val.value != forwarding_column_name:
                        continue
                    forward_idx = val.column
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
                    self.__classifier.add_potential_match(final_path)
                    # there shouldn't be anymore data in this row
                    break
                if val.column == forward_idx and re.match(r"\.xlsx", val.value):
                    # forwarding is on -> names should be in the table so only look for values in the new file
                    self.__follow_to_file(val.value, value_name_pairs, "{}/{}".format(path, sheet.title))
                    # TODO: continue here -> check if the file even exists
        return

    def _check_column_wise(self, sheet: Worksheet, value_name_pairs: Iterator[Tuple[str, str]], path: str) -> None:
        """
        Iterates through the columns of the sheet given and tries to match the given list of value-URI-pairs in a
        column-wise fashion. If a match could be made the resulting path is pushed into the classifier

        :param sheet: the sheet to search for matches
        :param value_name_pairs: the stuff (hopefully) to find in the sheet given
        :param path: the path to the current sheet (excluding the sheet itself)
        """
        lowest_header_col: int = 0
        header_color = self.__config["header_{}".format(sheet.title)]
        for values in sheet.iter_cols():
            val: Cell
            first_result: XlsxProcessor.CellMatchStruct = XlsxProcessor.CellMatchStruct(False)
            for val in values:
                # skip empty cells
                if val.value is None:
                    continue
                # housekeeping for the final path
                if val.fill.bgColor.rgb == header_color and val.col_idx >= lowest_header_col:
                    lowest_header_col = val.col_idx
                    # the header is not of interest in a row-wise table as the classifier ignores header names
                    continue
                if not first_result.success:
                    first_result = self.__match_cell_properties_to(val, value_name_pairs)
                    if not first_result.success:
                        continue
                # in the team file the cell holds the name and its size determines the size property -> so check this
                # one against the expected value, too
                if first_result.success:
                    second_result = self.__match_expected_in(val, first_result, True)
                    if not second_result[0]:
                        continue
                    # assemble the path for the classifier it can match later on
                    col_data_start = get_column_letter(lowest_header_col + 1)
                    value_cell = self.__to_linear_cell_address(False, col_data_start, int(second_result[1].value_id),
                                                               second_result[1].value_property)
                    name_cell = self.__to_linear_cell_address(False, col_data_start, int(second_result[1].name_id),
                                                              second_result[1].name_property)
                    final_path = "{}/{}/@{};{}".format(path, sheet.title, value_cell, name_cell)
                    self.__classifier.add_potential_match(final_path)
                    # there shouldn't be anymore data in this row
                    break
        return

    def _check_as_cross_table(self, sheet: Worksheet, value_name_pairs: Iterator[Tuple[str, str]], path: str) -> None:
        """
        Iterates through the sheet and tries to determine if the sheet could contain a cross table where names and
        values are distributed along a column and a row and their matching is indicated by a 'X' in the field below

        :param sheet: the sheet to search for matches
        :param value_name_pairs: the stuff (hopefully) to find in the sheet given
        :param path: the path to the current sheet (excluding the sheet itself)
        """
        # in a cross table everything should just stand in the table: so check if the values or the pairs can be found
        # in a column and go from there
        def check_line_for_list_entries(line: List[Cell], to_find: Iterator[str]) -> (bool, int):
            """
            Checks if the given column or row does contain at least 50% of the entries from the "list" given. If so true
            is returned as the index of the first match

            :param line: the column or row to search for a value of to_find
            :param to_find: a list of values which to be hoped to be found in the column
            :return: if a match could be found and at which index
            """
            # create a working copy
            work = list(to_find)
            start_len = float(len(work))
            earliest_hit = 1000
            for cell in line:
                current_val = str(cell.value)
                if current_val in work:
                    work.remove(current_val)
                    if cell.row < earliest_hit:
                        earliest_hit = cell.row
            if float(len(work)) / start_len <= 0.5:
                # if more about 50% could be found it can be assumed that it makes sense to continue
                return True, earliest_hit
            return False, -1

        def find_name_in_col(column: Iterator[Cell], to_find: str) -> Cell:
            """
            Goes through the given column and returns the cell the value was found in else None

            :param column: the column to search for the keyword
            :param to_find: the keyword to find as value in one of the cells
            :return: the row index the value was found in
            """
            for cell in column:
                if cell.value == to_find:
                    return cell
            return None

        def find_x(start_index: int) -> Cell:
            """
            Returns the first cell in which a "x" could be found starting from the row index given
            :param start_index: from which index to start looking for a x
            :return: the first cell that contains a x
            """
            for row in sheet.iter_rows(min_row=start_index):
                row_cell: Cell
                for row_cell in row:
                    if str(row_cell.value) == "x" or str(row_cell.value) == "X":
                        return row_cell
            return None

        def find_data_field_start(to_scan: Iterator[Cell], is_row: bool) -> int:
            """
            Triggers on the first color change of cell background color that does come after a cell that was not white

            :param to_scan: the row / column to check for the color change
            :param is_row: if the iterator at hand represents a row or a column
            :return: the index of column or row the new color appeared
            """
            header_color = ""
            for cell in to_scan:
                if cell.fill.bgColor.rgb == "00000000" and header_color == "":
                    continue    # ignore white cells which might be around the table itself
                if header_color == "":
                    header_color = cell.fill.bgColor.rgb
                elif cell.fill.bgColor.rgb != header_color:
                    if is_row:
                        return cell.column
                    return cell.row

        intermediate_value_name_separation = zip(*value_name_pairs)
        values = next(intermediate_value_name_separation)
        names = next(intermediate_value_name_separation)
        for col_iter in sheet.iter_cols():
            col = list(col_iter)    # transform it so we can search through it multiple times
            success_names, name_index = check_line_for_list_entries(col, names)
            success_values, value_index = check_line_for_list_entries(col, values)
            if not (success_names or success_values):
                continue
            # find the first row which contains a 'x' and try to find it's matching value in that column
            if success_names:
                x_cell = find_x(name_index)
            else:
                x_cell = find_x(value_index)
            if x_cell is None:
                # does not seem to be a cross table: just abort
                return
            # TODO: a proper implementation might better check for multiple 'X'
            # find the corresponding value or name
            found_one = sheet["{}{}".format(col[0].column_letter, x_cell.row)]
            counterpart_content = values[names.index(found_one.value)] if success_names else names[values.index(
                found_one.value)]
            counterpart_cell = find_name_in_col(sheet[x_cell.column], counterpart_content)
            if counterpart_cell is None:
                # seems like it isn't a cross table after all
                return
            # perform a final check if the column contains eg. most of the names the row should contain most of the
            # values
            confirmed, _ = check_line_for_list_entries(sheet[counterpart_cell.row], names if success_values else values)
            if not confirmed:
                # most of the expected counter values could not be found in a row -> doesn't seem to be cross table
                return
            # derive the start of the center field from the color changes in the detected row and column -> this is
            # should be more robust then working with the names itself which might be incomplete
            field_start_col = get_column_letter(find_data_field_start(sheet[x_cell.row], True))
            field_start_row = find_data_field_start(sheet[counterpart_cell.column_letter], False)
            # check which belongs where: are names in the column or values
            top_bar_pos = "{}${}".format(field_start_col, counterpart_cell.row)
            side_bar_pos = "${}{}".format(col[0].column_letter, field_start_row)
            values_start = side_bar_pos if success_values else top_bar_pos
            names_start = top_bar_pos if success_values else side_bar_pos
            current_path = "{}/{}/@{}{};{};{}".format(path, sheet.title, field_start_col, field_start_row, values_start,
                                                      names_start)
            self.__classifier.add_potential_match(current_path)
            # the cross table has been identified, next attempts should fail anyway so abort search
            return

    def __includes_forwarding(self, sheet_name: str) -> Tuple[bool, str]:
        """
        Checks if the given sheet name is registered with a column which forwards to another file

        :param sheet_name: the name to check for
        :return: a tuple which contains if forwarding is to be expected and the column which is to be used for that
        """
        # as this project has only one root file the separation is simple
        names = self.__config[self.FORWARDING_KEY].split('/')
        if len(names) != 2:
            raise ValueError("The config file is wrong: expecting a path made of sheet/column. Received: " +
                             self.__config[self.FORWARDING_KEY])
        if names[0] != sheet_name:
            return False, ""
        return True, names[1]

    def __follow_to_file(self, file_name: str, value_name_pairs: Iterator[(str, str)], current_path: str):
        file_path = self.__nested_xlsx_dir + file_name + file_name
        if not os.path.exists(file_path):
            raise NoMatchCandidateException("Could not find a file under: " + file_path)
        wb = load_workbook(file_path)
        for sheet in wb.sheetnames:
            self._search_sheet_for_values(value_name_pairs, )

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
    def __scan_cell_line_for(value_name_pairs: Iterator[Tuple[str, str]],
                             to_scan: Iterator[Cell],
                             forward_index: int = -1) -> CellLineResult:
        pass

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
