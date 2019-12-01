from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Color, PatternFill, Alignment
from typing import Dict, List, Tuple
import json
import re
from creation.SectionCreator import SectionCreator


class InitializationException(Exception):
    """
    Exception is intended for situations when a class should have been provided
    with data before but wasn't
    """


class Creator:
    """
    The class which creates the files which the learning algorithm can use for
    training
    """

    # constants
    WORKER_SHEET = "Workers"
    SECTION_SHEET = "Sections"

    class _DataStruct:
        """
        Works as a container / struct to organize the data for a worker
        """
        attributes: Dict[str, str]
        skills: List[str]

        def __init__(self):
            self.attributes = {}
            self.skills = []

        def __str__(self):
            s = "Content:\n"
            for attr in self.attributes:
                s += "{} : {}\n".format(attr, self.attributes[attr])
            return s + "List content: {}".format(str(self.skills))

    __sectionList: List[_DataStruct] = []
    __workerList: List[_DataStruct] = []
    __assignments: List[Tuple[_DataStruct, _DataStruct]]

    def read_from_json(self, path_to_workers: str, path_to_sections: str) -> None:
        """
        Reads in the data from the 2 JSON-files in order to create data from
        them
        :param path_to_workers: the path to the file containing the worker
                                definitions in JSON formatting
        :param path_to_sections: the path to the file containing the section
                                 definitions in JSON formatting
        """

        def read_in(path, target):
            with open(path) as json_file:
                entities = json.load(json_file)
                for e in entities:
                    current = Creator._DataStruct()
                    for attr in e:
                        if attr == "Skills":
                            current.skills = e[attr]
                            continue
                        current.attributes[attr] = e[attr]
                    target.append(current)

        for t in ["workers", "sections"]:
            if t == "workers":
                read_in(path_to_workers, self.__workerList)
            elif t == "sections":
                read_in(path_to_sections, self.__sectionList)
            else:
                raise AttributeError(
                    "No implementation to push {} to the internal members".format(t))

    def create_xlsx(self, file_name: str = "../data.xlsx") -> None:
        if not self._has_internal_data():
            raise InitializationException("Members seem not been initialized with data")
        # create the sheet with the worker data
        wb = Workbook()
        # a blank sheet is created by default: use this instead of creating a new one
        current = wb.active
        current.title = self.WORKER_SHEET
        # foreach property of worker
        self._create_single_table(current, self.__workerList, 4, 2, self.WORKER_SHEET)
        # create the sheet with the sections
        current = wb.create_sheet(self.SECTION_SHEET)
        self._create_single_table(current, self.__sectionList, 4, 2, self.SECTION_SHEET)
        # create the sheet where to every skill of a section is corresponded with a workers skill
        current = wb.create_sheet("Affiliations")
        self._create_cross_table(current, 2, 2, "Affiliations")
        wb.save(file_name)

    def create_xml(self, name: str) -> None:
        if not self._has_internal_data():
            raise InitializationException("Members seem not been initialized with data")

    def _has_internal_data(self) -> bool:
        """
        Checks if the members are filled with data else false is returned
        :return: true if all members hold data and are not empty lists
        """
        return len(self.__sectionList) != 0 and len(self.__workerList) != 0

    def _create_single_table(self, workbook, data: List[_DataStruct], start_row: int, start_column: int, name: str,
                             offset_row: int = 2, offset_col: int = 0) -> None:
        """
        Creates a row table dedicated to the data given
        :param workbook: the to write the data in
        :param data: the actual data to write (should either be worker or section descriptions)
        :param start_row: the row the table heading should be placed in
        :param start_column: the column the table heading should start
        :param name: the name of the table to use as heading
        :param offset_row: set this value for vertical displacement between the heading and the table header
        :param offset_col: set this value for horizontal displacement between the heading the the table header
        """
        def replace_spaces(to_transform: str) -> str:
            """
            Replaces all whitespaces with underscores in the string given
            """
            return re.sub(r"\s", "_", to_transform)

        workbook.cell(row=start_row, column=start_column).value = name
        # use the first data point as template
        header_keys = data[0].attributes.keys()
        # create the table header
        header_fill = PatternFill(start_color='FFFFFF00',
                                  end_color='FFFFFF00', fill_type='solid')
        header_alignment = Alignment(horizontal='center')
        table_row = start_row + offset_row
        current_col = start_column + offset_col
        for key in header_keys:
            current_cell = workbook.cell(row=table_row, column=current_col)
            # skip the exception
            if key == SectionCreator.TEAM_KEY:
                # override the value
                key_content = "section file"
            else:
                key_content = key
            current_cell.value = key_content
            # do some styling
            current_cell.fill = header_fill
            current_cell.alignment = header_alignment
            # adapt the width in the process
            col_letter = get_column_letter(current_col)
            # use the first worker as a template again
            # take whatever is longer: key or content
            content_width = len(str(data[0].attributes[key]))
            key_width = len(key)
            width = key_width if key_width > content_width else content_width
            workbook.column_dimensions[col_letter].width = 1.8 * width
            current_col += 1
        # update the row "pointer" below the header
        table_row += 1
        for y in range(len(data)):
            current_col = start_column + offset_col
            for key in header_keys:
                cell = workbook.cell(row=table_row + y, column=current_col)
                val = data[y].attributes[key]
                if key == SectionCreator.TEAM_KEY:
                    # override
                    val = replace_spaces(data[y].attributes["Name"]) + ".xlsx"
                cell.value = self.__val_to_string(val)
                current_col += 1

    def _create_cross_table(self, workbook, start_row: int, start_column: int, table_tile: str, offset_row: int = 2,
                            offset_col: int = 0):
        # worker_data: List[_DataStruct], section_data: List[_DataStruct] come as class members
        # start with creating the header
        workbook.cell(row=start_row, column=start_column).value = table_tile
        current_row = start_row + offset_row + 1    # start one row below and merge all section cells afterwards
        # set row height for the section skills based on the first entry using it as blueprint for length estimation
        workbook.row_dimensions[current_row].height = len(self.__sectionList[0].skills[0]) * 5 * 1.7
        # and for the names
        workbook.row_dimensions[current_row-1].height = len(self.__sectionList[0].attributes["Name"]) * 10
        # +2 for the col as downwards the columns for the worker and the abilities are required
        current_column = start_column + offset_col + 2
        # set the styling
        section_fill = PatternFill(start_color='FFFF9933', end_color='FFFF9933', fill_type='solid')
        for section in self.__sectionList:
            col_section_start = current_column
            for skill in section.skills:
                # adapt the column width where required
                workbook.column_dimensions[get_column_letter(current_column)].width = 3
                active = workbook.cell(row=current_row, column=current_column)
                active.value = skill
                active.alignment = Alignment(text_rotation=90)
                active.fill = section_fill
                current_column += 1
            # now merge the upper cells and insert the section name
            workbook.merge_cells(start_row=current_row-1, start_column=col_section_start, end_row=current_row-1,
                                 end_column=current_column-1)
            section_cell = workbook.cell(row=current_row-1, column=col_section_start)
            section_cell.value = section.attributes["Name"]
            section_cell.alignment = Alignment(text_rotation=90, horizontal='center')
            section_cell.fill = section_fill

    def __assign(self, workers: List[_DataStruct], sections: List[_DataStruct]):
        ## assign the workers to their section on a random basis -> use a new list and shuffle it
        #shuffled_workers = list(workers)
        #assigned = ()
        #for w in range(len(shuffled_workers)):
        #    # start with assigning workers which fully match the job description
        #
        #    self.__assignments.append()     # add the pairing here
        pass

    @staticmethod
    def __val_to_string(val) -> str:
        if not isinstance(val, list):
            # just fallback to the python default
            return str(val)
        if not val:
            # means the list is empty
            return ""
        list_str = str(val[0])
        for i in range(1, len(val)):
            list_str += ", {}".format(val[i])
        return list_str


if __name__ == "__main__":
    c = Creator()
    c.read_from_json("../workers.json", "../sections.json")
    c.create_xlsx()
