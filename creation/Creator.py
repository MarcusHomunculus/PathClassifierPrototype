from openpyxl import Workbook
from typing import Dict, List
import json
import math


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

	#
    # def __init__(self):
    #	"""
    #	The constructor
    #	"""
    #	pass

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
        current.title = "Workers"
        current['B2'] = "Workers"
        # foreach property of worker
        self._create_worker_table(current, 4, 2)
        wb.save(file_name)
        # create the sheet with the sections
        wb.create_sheet("Sections")
        # create the sheet where to every section a worker is assigned
        wb.create_sheet("Assignments")

    def create_xml(self, name: str) -> None:
        if not self._has_internal_data():
            raise InitializationException("Members seem not been initialized with data")
            
    def _has_internal_data(self) -> bool:
        """
        Checks if the members are filled with data else false is returned
        :return: true if all members hold data and are not empty lists
        """
        return len(self.__sectionList) != 0 and len(self.__workerList) != 0
       
    def _create_worker_table(self, workbook, start_row: int, start_column: int):
        row_range = range(len(self.__workerList))
        # use the first worker as template
        worker_keys = self.__workerList[0].attributes.keys()
        # create the table header
        current_col = start_column
        for key in worker_keys:
            workbook.cell(row=start_row, column=current_col).value = str(key)
            current_col += 1
        for y in row_range:
            current_col = start_column
            # TODO: remove current_worker after debug
            current_worker = self.__workerList[y]
            name = current_worker.attributes["Name"]
            print("Current workers name is " + name)
            for key in worker_keys:
                cell = workbook.cell(row=start_row + 1 + y, column=current_col)
                cell.value = str(self.__workerList[y].attributes[key])
                current_col += 1

#    @staticmethod
#    def _build_table_coordinate(column: int, row: int) -> str:
#        letter_pool = [chr(i) for i in range(ord('a'), ord('a') + 26)]
#        def to_multi_col(col_idx):
#            letter_cnt = int(math.ceil(col_idx / 26))
#            result = ""
#            for ii in range(letter_cnt, 0, -1):
#                idx = col_idx % (ii * 26)
#                result += letter_pool[idx]
#            return result
#        return to_multi_col(column) + str(row - 1)    # -1 as xlsx starts indexing at 1
#       
if __name__ == "__main__":
    c = Creator()
    c.read_from_json("../workers.json", "../sections.json")
    c.create_xlsx()
