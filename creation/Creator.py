from openpyxl import Workbook
from typing import Dict, List
import json


class InitializationException(Exception):
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

    def read_from_json(self, path_to_workers: str, path_to_sections: str):
        with open(path_to_workers) as json_file:
            workers = json.load(json_file)
            for w in workers:
                current = Creator._DataStruct()
                for attr in w:
                    if attr == "Skills":
                        current.skills = w[attr]
                        continue
                    current.attributes[attr] = w[attr]
                self.__workerList.append(current)
        for w in self.__workerList:
            print(w)

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
