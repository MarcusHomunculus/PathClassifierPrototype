from __future__ import annotations
from typing import List, Tuple, Iterator, Dict
import re
import os
from openpyxl import load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.utils import get_column_letter, column_index_from_string

from matcher.internal.enum.CellPropertyType import CellPropertyType
from matcher.internal.data_struct.CellMatching import CellMatchingStruct, CellMatchResult
from matcher.internal.data_struct.CellPositioning import CellPosition, CellPositionStruct, CellPositionStructType
from classifier.BinClassifier import BinClassifier
from classifier.error.MatchExceptions import NoMatchCandidateException


class XlsxProcessor:

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

    class ForwardHelperCluster:
        struct: CellMatchingStruct
        value_position: CellPosition
        final_path: str

        def __init__(self, struct: CellMatchingStruct, value_position: CellPosition, path: str):
            """
            Creates an instance of a helper struct to bundle data from a forwarding attempt. The struct is should be the
            same as the one received with the forwarding command and is explicitly returned to express the intention to
            change it's state

            :param struct: the potentially updated struct received
            :param value_position: the position of the value found as cell coordinate
            :param path: the path to the sheet where the value can be found
            """
            self.struct = struct
            self.value_position = value_position
            self.final_path = path

        def to_tuple(self) -> Tuple[CellMatchingStruct, CellPosition, str]:
            """
            Allows to transform the cluster to a tuple for inline unpacking

            :return: the structs members clustered as a tuple
            """
            return self.struct, self.value_position, self.final_path

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

    def _search_sheet_for_values(self, value_name_pairs: Iterator[Tuple[str, str]], sheet: Worksheet,
                                 path: str) -> None:
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

    def _check_row_wise(self, sheet: Worksheet, value_name_pairs: Iterator[Tuple[str, str]],
                        path: str) -> CellPositionStruct:
        """
        Iterates through the rows of the sheet given and tries to match the given list of value-URI-pairs in a row-wise
        fashion. If a match could be made the resulting path is pushed into the classifier

        :param sheet: the sheet to search for matches
        :param value_name_pairs: the stuff (hopefully) to find in the sheet given
        :param path: the path to the current sheet (excluding the sheet itself)
        :return a LineResultStruct if only a value has been found: this is important for forwarded searches else an
                invalid / empty struct
        """
        current_sheet_path = "{}/{}".format(path, sheet.title)
        lowest_header_row: int = 0
        forward_index = -1
        handle_forwarding, forwarding_column_name = self.__includes_forwarding(sheet.title)
        header_color = self.__config["header_{}".format(sheet.title)]
        row_index = -1
        for row in sheet.iter_rows():
            row_index += 1
            result = self.__scan_cell_line_for(row, value_name_pairs, forward_index, header_color,
                                               "" if not handle_forwarding else forwarding_column_name)
            if result.read_result == CellPositionStructType.NO_FINDING:
                continue
            elif result.read_result == CellPositionStructType.HEADER_FOUND:
                lowest_header_row = row_index
                if result.contains_header_forwarding_position():
                    forward_index = column_index_from_string(result.name_or_forward_position.column)
                continue
            # else data has been found
            if result.match_struct.success_type == CellMatchResult.VALUE_FOUND:
                # only a value has been found -> forward the information to the caller -> but if no header has been
                # found the orientation is probably bogus
                if lowest_header_row > 0:
                    return result
                return CellPositionStruct.create_no_find()
            elif result.match_struct.success_type != CellMatchResult.ALL_FOUND:
                # this case shouldn't exist in reality yet cover it to be on the safe side
                continue
            # else a pair has been detected -> collect all the required data and push the result into the classifier
            row_data_start = lowest_header_row + 1
            value_cell = self.__to_linear_cell_address(False, result.value_position.column, row_data_start,
                                                       result.value_position.read_type)
            value_path = current_sheet_path if not result.contains_value_forwarding_path() else result.value_path
            final_path = "{}/@{};".format(value_path, value_cell)
            name_cell = self.__to_linear_cell_address(False, result.name_or_forward_position.column, row_data_start,
                                                      result.name_or_forward_position.read_type)
            if result.contains_value_forwarding_path():
                # prepend the current path to the name path to indicate that both differ
                name_cell = "{}/@{}".format(current_sheet_path, name_cell)
            else:
                name_cell = "@{}".format(name_cell)
            final_path += name_cell
            self.__classifier.add_potential_match(final_path)
        # if something was found it has been pushed to the classifier already -> so no need to return anything
        return CellPositionStruct.create_no_find()

    def _check_column_wise(self, sheet: Worksheet, value_name_pairs: Iterator[Tuple[str, str]],
                           path: str) -> CellPositionStruct:
        """
        Iterates through the columns of the sheet given and tries to match the given list of value-URI-pairs in a
        column-wise fashion. If a match could be made the resulting path is pushed into the classifier

        :param sheet: the sheet to search for matches
        :param value_name_pairs: the stuff (hopefully) to find in the sheet given
        :param path: the path to the current sheet (excluding the sheet itself)
        """
        current_sheet_path = "{}/{}".format(path, sheet.title)
        lowest_header_col: int = 0
        forward_index = -1
        handle_forwarding, forwarding_row_name = self.__includes_forwarding(sheet.title)
        header_color = self.__config["header_{}".format(sheet.title)]
        col_index = -1
        for column in sheet.iter_cols():
            col_index += 1
            result = self.__scan_cell_line_for(column, value_name_pairs, forward_index, header_color,
                                               "" if not handle_forwarding else forwarding_row_name)
            if result.read_result == CellPositionStructType.NO_FINDING:
                continue
            elif result.read_result == CellPositionStructType.HEADER_FOUND:
                lowest_header_col = col_index
                if result.contains_header_forwarding_position():
                    forward_index = result.name_or_forward_position.row
                continue
            # else data has been found
            if result.match_struct.success_type == CellMatchResult.VALUE_FOUND:
                # only a value has been found -> forward the information to the caller -> but if no header has been
                # found the orientation is probably bogus
                if lowest_header_col > 0:
                    return result
                return CellPositionStruct.create_no_find()
            elif result.match_struct.success_type != CellMatchResult.ALL_FOUND:
                # this case shouldn't exist in reality yet cover it to be on the safe side
                continue
            # else a pair has been detected -> collect all the required data and push the result into the classifier
            col_data_start = get_column_letter(lowest_header_col + 1)
            value_cell = self.__to_linear_cell_address(True, col_data_start, result.value_position.row,
                                                       result.value_position.read_type)
            value_path = current_sheet_path if not result.contains_value_forwarding_path() else result.value_path
            final_path = "{}/@{};".format(value_path, value_cell)
            name_cell = self.__to_linear_cell_address(True, col_data_start, result.name_or_forward_position.row,
                                                      result.name_or_forward_position.read_type)
            if result.contains_value_forwarding_path():
                # prepend the current path to the name path to indicate that both differ
                name_cell = "{}/@{}".format(current_sheet_path, name_cell)
            else:
                name_cell = "@{}".format(name_cell)
            final_path += name_cell
            self.__classifier.add_potential_match(final_path)
        # if something was found it has been pushed to the classifier already -> so no need to return anything
        return CellPositionStruct.create_no_find()

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

    def _follow_forward_to(self, file: str, testing_struct: CellMatchingStruct) -> ForwardHelperCluster:
        # TODO: first check if the file even exists
        pass

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
            self._search_sheet_for_values(value_name_pairs, sheet, current_path)

    def __scan_cell_line_for(self, to_scan: Iterator[Cell],
                             value_name_pairs: Iterator[(str, str)] = None,
                             forward_index: int = -1,
                             header_color: str = "",
                             forward_name: str = "") -> CellPositionStruct:
        """
        Goes through the iteration of cells and checks if it can find useful information in it. The result is returned
        in form of struct which holds data depending on the found data

        :param to_scan: the iterator for a collection of cells (which is usually either a column or a row)
        :param value_name_pairs: the values and names to find in the sheet. Set if you want to find these data
        :param forward_index: set this parameter if at this given index the content has to be interpreted as file name
        :param header_color: set this value if a header has to be detected
        :param forward_name: set this value if a header field containing this value indicates forwarding
        :return: a situation dependent initialized instance of LineResultStruct
        """
        if value_name_pairs is None:
            value_name_pairs = []
        current_idx = 0     # which results in starting the iteration with 1 which is the start for excel
        value_path = ""
        result_struct = CellMatchingStruct(value_name_pairs)
        value_position = CellPosition.create_invalid()
        name_position = CellPosition.create_invalid()
        is_header = False
        for cell in to_scan:
            current_idx += 1
            if cell.value is None:
                # skip the empty cell
                continue
            if cell.fill.bgColor == header_color:
                if cell.value == forward_name:
                    # return immediately as only one forwarding index is expected
                    # -> if multiple are required use a state machine
                    return CellPositionStruct.create_header_found(CellPosition.create_from(cell,
                                                                                           CellPropertyType.CONTENT))
                is_header = True
                continue
            # now the cell should contain some data -> find out if it is data of interest
            if current_idx == forward_index:
                result = self._follow_forward_to(cell.value, result_struct)
                # write directly to value_position as the name shouldn't be found in the forwarding file
                # -> this would beat the whole purpose of the forwarding
                result_struct, value_position, value_path = result.to_tuple()
            else:
                cell_data = XlsxProcessor.__extract_cell_properties(cell)
                for data in cell_data.keys():
                    result = result_struct.test_value(data)
                    if result == CellMatchResult.NAME_FOUND:
                        name_position = CellPosition.create_from(cell, cell_data[data])
                    elif result == CellMatchResult.VALUE_FOUND:
                        value_position = CellPosition.create_from(cell, cell_data[data])
            if name_position.is_valid() and value_position.is_valid():
                # no reason to continue -> everything has been found
                return CellPositionStruct.create_data_pair_found(result_struct, value_position, name_position)
        # keep this separated as their separation ensures that header and data are detected in different lines
        # -> prefer the value over the header as no detected header means no correctly detected table
        if value_position.is_valid():
            return CellPositionStruct.create_value_found(result_struct, value_position, value_path)
        if is_header:
            return CellPositionStruct.create_header_found(CellPosition.create_invalid())
        return CellPositionStruct.create_no_find()

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
