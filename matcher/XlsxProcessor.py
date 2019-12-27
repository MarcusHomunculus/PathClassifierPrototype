from typing import List, Tuple, Iterator, Dict
import re
from openpyxl import load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet

from classifier.BinClassifier import BinClassifier


class XlsxProcessor:

    class CellMatchStruct:
        success: bool
        expected: str
        found_one_is_name: bool

        def __init__(self, success: bool, expected: str = "", found_name: bool = False):
            """
            The constructor
            :param success: if the search for a value or name yielded a hit
            :param expected: the value or name to be found to match it to the content found
            :param found_name: true if the content found was the name else the value has been found
            """
            # start with a sanity check
            if success and expected == "":
                raise ValueError("Received an empty expected value were a string must be")
            self.success = success
            self.expected = expected
            self.found_one_is_name = found_name

    FORWARDING_KEY = "forwarding_on"
    TEMPLATE_CELL_ADDRESS_ROW_WISE = "${}{}:{}"
    TEMPLATE_CELL_ADDRESS_COL_WISE = "{}${}:{}"
    CELL_PROPERTY_CONTENT = "c"
    CELL_PROPERTY_WIDTH = "w"

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

    def match_given_values_in(self, value_name_pairs: Iterator[Tuple[str, str]], file_path: str) -> None:
        """
        Manages itself through the given xlsx-file and and tries to match the given pairs in the files (somewhere)

        :param value_name_pairs: a list of tuples with values and their corresponding URI
        :param file_path: the path to the file to match the values in
        """
        wb = load_workbook(file_path, True)
        sheet_names = wb.sheetnames
        for sheet in sheet_names:
            self.__search_sheet_for_values(value_name_pairs, wb[sheet], file_path)

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
        def get_data_start_of(column: Iterator[Cell]) -> int:
            """
            Iterates through the background color of the cells of the column given and returns the first row the
            (in the config file) specified header color is not used anymore

            :param column: the column to check for the first row of data lines
            :return: the row which should contain the first batch of data. If nothing could be found -1
            """
            header_hook = False
            header_color = self.__config["header_{}".format(sheet.title)]
            for item in column:
                if item.style.bg_color == header_color:
                    header_hook = True
                elif header_hook and item.style.bg_color != header_color:
                    return item.row
            return -1

        for values in sheet.iter_rows():
            # keep the index to check that the value belongs to the name and vice versa
            col_id = ""
            col_val = ""
            expected = ""  # an empty string resolves to false if converted to boolean
            for val in values:
                # skip empty cells
                if val.value is None:
                    continue
                if not expected:
                    result = self.__match_cell_properties_to(val, value_name_pairs)
                    if not result.success:
                        continue
                    expected = result.expected
                    if result.found_one_is_name:
                        col_id = val.column_letter
                    else:
                        col_val = val.column_letter
                # in the team file the cell holds the name and its size determines the size property -> so check this
                # one against the expected value, too
                if expected:
                    props = self.__extract_cell_properties(val)
                    for prop in props.keys():
                        if prop == expected:
                            col_id = val.column_letter if not col_id else col_id
                            col_val = val.column_letter if not col_val else col_val
                            # find the first line after the header once -> as the header should at one level the result
                            # should be true for both columns: so just pick one
                            row_data_start = get_data_start_of(sheet.iter_rows(col_id))
                            if row_data_start == -1:
                                # something went wrong: better abort
                                break
                            # assemble the path for the classifier it can match later on
                            final_path = "{}/{}/@{};{}".format(path, sheet.title,
                                                               self.__to_linear_cell_address(False, col_val,
                                                                                             row_data_start, props[prop]
                                                                                             ),
                                                               self.__to_linear_cell_address(False, col_id,
                                                                                             row_data_start,
                                                                                             self.CELL_PROPERTY_CONTENT)
                                                               )
                            self.__classifier.add_potential_match(final_path)
                            return
        return

    @staticmethod
    def __match_cell_properties_to(to_read_from: Cell, value_name_pairs: Iterator[Tuple[str, str]]) -> CellMatchStruct:
        """
        Extracts all supported properties of a cell (including its content) and checks if one property can be matched
        to the list of value name pairs given. This function ignores the property of the cell matched on because it
        is assumed that the first match will be on the identifier which should be the content of the cell anyway

        :param to_read_from: the cell to check the properties of
        :param value_name_pairs: a list of values expected
        :return: a struct containing data for further processing
        """
        for to_find in value_name_pairs:
            for prop in XlsxProcessor.__extract_cell_properties(to_read_from).keys():
                if prop == to_find[0]:
                    # return that the value has been found
                    return XlsxProcessor.CellMatchStruct(True, to_find[1], False)
                elif prop == to_find[1]:
                    # return that the name has been found
                    return XlsxProcessor.CellMatchStruct(True, to_find[0], True)
        # means nothing has been found: return an invalid struct
        return XlsxProcessor.CellMatchStruct(False)

    @staticmethod
    def __extract_cell_properties(to_extract_from: Cell) -> Dict[str, str]:
        """
        Takes the cell an creates a list of properties from it

        :param to_extract_from: the cell the properties are wanted from
        :return: a list of all properties supported
        """
        return {str(to_extract_from.value): XlsxProcessor.CELL_PROPERTY_CONTENT}

    @staticmethod
    def __to_linear_cell_address(is_fixed_row: bool, col: str, row: int, property_identifier: str) -> str:
        """
        Inserts the given arguments into the template given. This function is merely a reminder to use a template

        :param is_fixed_row: if the template should assume a row-wise reading scheme or a column-wise scheme
        :param col: the column to insert
        :param row: the row to insert
        :param property_identifier: the identifier of the cell property to use as source
        :return: a properly formatted string to be used as cell address
        """
        if is_fixed_row:
            template = XlsxProcessor.TEMPLATE_CELL_ADDRESS_ROW_WISE
        else:
            template = XlsxProcessor.TEMPLATE_CELL_ADDRESS_COL_WISE
        return template.format(col, row, property_identifier)
