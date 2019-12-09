from typing import List
import toml


class XmlXlsxMatcher:

    FORWARDING_KEY = "forwarding_on"

    __config = {}

    def __init__(self, path_to_config: str, path_root_xlsx: str, nested_xlsx_dir: str = "."):
        """
        The constructor

        :param path_to_config: the path to the config file
        :param path_root_xlsx: the path to the main Excel file
        :param nested_xlsx_dir: the path to the other Excel files which the root file might reference to
        """
        self.__read_config(path_to_config)

    def __read_config(self, path_to_file: str) -> None:
        """
        Reads in the config file

        :param path_to_file: the path to the TOML file to read
        """
        config = {}
        with open(path_to_file, "r", encoding="utf-8") as c:
            config.update(toml.load(c))
        self.__config = config

    def _axis_is_forwarding(self, name: str) -> bool:
        """
        Returns if the column (or row) references another Excel file which might be followed
        :param name: the identifier of the axis (column or row)
        :return: true if the program should open the file and search for data there
        """
        if XmlXlsxMatcher.FORWARDING_KEY not in self.__config:
            return False    # no forwarding specified
        if self.__config[XmlXlsxMatcher.FORWARDING_KEY] != name:
            return False
        return True

    def _get_main_nodes(self) -> List[str]:
        """
        Extracts the names of the anchor nodes in the XML from the config

        :return: an iterable of the nodes which should be trained
        """
        raw_list = self.__config["List_nodes"]
        return raw_list.split(",")

    def _get_universal_id(self):
        """
        Returns the identifier which is used to distinguish the main nodes from each other

        :return: the identifier which can be used for matching
        """
        return self.__config["uri"]
