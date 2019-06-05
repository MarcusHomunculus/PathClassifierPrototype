from openpyxl import Workbook
from typing import Dict, List
import json


class InitializationException(Exception):
    """
    Exception is intended for situations when a class should have been provided
    with data before but wasn't
    """
    pass


class Creator:
    """
    The class which creates the files which the learning algorithm can use for
    training
    """

    class _DataStruct:
        """
        Works as a container / struct to organize the data for a worker
        """
        attributes: Dict[str, str] = {}
        skills: List[str] = []

        def __str__(self):
            s = "Content:\n"
            for attr in self.attributes:
                s += "{} : {}\n".format(attr, self.attributes[attr])
            return s + "List content: {}".format(self.skills)

    __sectionList: List[_DataStruct] = []
    __workerList: List[_DataStruct] = []

    def __init__(self):
        """
        The constructor
        """
        pass

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
                workers = json.load(json_file)
                for w in workers:
                    current = Creator._DataStruct()
                    for attr in w:
                        if attr == "Skills":
                            current.skills = w[attr]
                            continue
                        current.attributes[attr] = w[attr]
                    target.append(current)
        for t in ["workers", "sections"]:
            if t == "workers":
                read_in(path_to_workers, self.__workerList)
            elif t == "sections":
                read_in(path_to_sections, self.__sectionList)
            else:
                raise AttributeError(
                    "No implementation to push {} to the internal members".format(t))

    def create_xlsx(self) -> None:
        if not self._has_internal_data():
            raise InitializationException("Members seem not been initialized with data")

        # create the basic file
        wb = Workbook()
        pass

    def create_xml(self, name: str) -> None:
        if not self._has_internal_data():
            raise InitializationException("Members seem not been initialized with data")
        pass

    def _has_internal_data(self) -> bool:
        """
        Checks if the members are filled with data else false is returned
        :return: true if all members hold data and are not empty lists
        """
        return len(self.__sectionList) != 0 and len(self.__workerList) != 0


if __name__ == "__main__":
    c = Creator()
    c.read_from_json("../workers.json", "../sections.json")
