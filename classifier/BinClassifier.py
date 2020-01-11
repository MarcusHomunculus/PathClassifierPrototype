from typing import List, Dict
import html

from classifier.internal.BinCollection import BinCollection
from classifier.error.MatchExceptions import MultipleMatchingCandidatesException


class BinClassifier:

    __mat: List[BinCollection]
    __last_source: str
    __result_buffer: Dict[str, str]

    def __init__(self):
        self.__mat = []
        self.__last_source = ""
        self.__result_buffer = {}

    def add_source_path(self, source: str) -> None:
        """
        Allows to set a path which all following potential matches will be assigned to. Except a new path is specified
        via add_source_path or add_potential_match

        :param source: the path to the data in the source file
        """
        self.__mat.append(BinCollection(source))
        self.__last_source = source

    def get_active_source_path(self):
        """
        Returns the path under which current matches would be added with add_potential_match() if no source path would
        be given

        :return: the active source file path
        """
        return self.__last_source

    def add_potential_match(self, match_path: str, source_path: str = "") -> None:
        """
        Allows to add a new sink path to an either already added source path or the source path specified

        :param match_path: the path to a potential match in the sink file
        :param source_path: the path to data in the source file
        """
        if source_path == "":
            source_path = self.__last_source
        if source_path == "" or match_path == "":
            raise ValueError("Can't operate with empty strings")
        for entry in self.__mat:
            if entry.get_key() == source_path:
                entry.add_matched_path(match_path)

    def train(self) -> None:
        """
        Performs the learning / matching based on the data received previously
        """
        for path_bin in self.__mat:
            path, success = path_bin.get_highest_match()
            if not success:
                raise MultipleMatchingCandidatesException("Found matches with same count for path {}".format(
                    path_bin.get_key()))
            self.__result_buffer[path] = path_bin.get_key()

    def dump_as_html(self, target_path: str) -> None:
        # TODO: write some nice docu here
        def get_template(name: str) -> str:
            # TODO: doc me
            with open("classifier/templates/{}.htm".format(name), "r") as template_file:
                return template_file.read()
        # retrieve a list of all paths registered from the sink file
        sink_path_set = set()
        for line in self.__mat:
            sink_path_set.update(line.get_potential_paths())
        # transform it to a list to ensure order
        sink_paths = list(sink_path_set)
        content = get_template("match_table")
        # creating the table header
        header_template = get_template("table_head")
        head_string = ""
        for sink_path in sink_paths:
            head_string += header_template.replace("[%PATH%]", html.escape(sink_path)) + "\n"
        # insert the table head
        content = content.replace("[%SINK_PATHS%]", head_string, 1)
        column_count = len(sink_paths) + 1      # +1 for the source path to the left
        # write to file
        if not target_path.endswith(".html"):
            target_path += ".html"
        print("Dumping classifier matrix as HTML into " + target_path)
        with open(target_path, "w+") as sink_file:
            sink_file.write(content)
