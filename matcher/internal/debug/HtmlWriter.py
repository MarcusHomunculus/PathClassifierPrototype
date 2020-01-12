from typing import List, Tuple, Set
import html


class HtmlWriter:

    _raw_data: List[Tuple[str, List[Tuple[str, int]]]]

    def __init__(self, raw_data: List[Tuple[str, List[Tuple[str, int]]]]):
        """
        The constructor

        :param raw_data: the data to construct the html data from
        """
        self._raw_data = raw_data

    def dump_as_html(self, target_path: str) -> None:
        """
        Creates a html-file containing the classifier data (received with the constructor) as a 2D table

        :param target_path: the file to write the html data into
        """
        def get_template(name: str) -> str:
            """
            Returns the content of the given htm-template as string
            """
            with open("matcher/internal/templates/{}.htm".format(name), "r") as template_file:
                return template_file.read()

        def assign_bin_class(current_bin: int, max_bin: int) -> str:
            """
            Returns the class label for CSS depending on the given bin-value in relation to the max-count for the row
            """
            if current_bin == 0:
                return "zero_val"
            if current_bin < max_bin:
                return "intermediate_val"
            return "max_val"

        # retrieve a list of all paths registered from the sink file
        sink_path_set: Set[str] = set()
        for line in self._raw_data:
            for pair in line[1]:
                sink_path_set.add(pair[0])
        # transform it to a list to ensure order
        sink_path_pool = list(sink_path_set)
        content = get_template("match_table")
        # creating the table header
        header_template = get_template("table_head")
        head_string = ""
        for sink_path in sink_path_pool:
            head_string += header_template.replace("[%PATH%]", html.escape(sink_path)) + "\n"
        # insert the table head
        content = content.replace("[%SINK_PATHS%]", head_string, 1)
        # now for the body
        row_template = get_template("table_row")
        cell_template = get_template("match_cell")
        table_body = ""
        for row in self._raw_data:
            source_path = row[0]
            current_row = row_template.replace("[%SOURCE_PATH%]", source_path)
            matrix_row_str = ""
            # first find the highest value for the current row
            max_count = -1
            for pair in row[1]:
                if pair[1] > max_count:
                    max_count = pair[1]
            # now assemble the string
            for sink_path in sink_path_pool:
                cell_no = self.__get_bin_count_for(source_path, sink_path)
                current_cell = cell_template.replace("[%COUNT%]", str(cell_no) + "\n")
                matrix_row_str += current_cell.replace("[%MATCH_TYPE%]", assign_bin_class(cell_no, max_count))
            table_body += current_row.replace("[%MATCHES%]", matrix_row_str)
        content = content.replace("[%BODY%]", table_body)
        # write to file
        if not target_path.endswith(".html"):
            target_path += ".html"
        print("Dumping classifier matrix as HTML into " + target_path)
        with open(target_path, "w+") as sink_file:
            sink_file.write(content)

    def __get_bin_count_for(self, source_path: str, sink_path: str) -> int:
        """
        Returns the number of increments for the given source-path-to-sink-path-registrations

        :param source_path: the path from the source file
        :param sink_path: the path to the sink path in question
        :return: the count of registrations for the given constellation
        """
        def get_pair_list(key: str) -> List[Tuple[str, int]]:
            """
            Extracts the list of path-count-pairs which belong to the given source path

            :param key: the source path to use as key
            :return: the list of registered paths and their count to the given key (-path)
            """
            for entry in self._raw_data:
                if entry[0] == key:
                    return entry[1]
        pair_list = get_pair_list(source_path)
        for pair in pair_list:
            if pair[0] == sink_path:
                return pair[1]
        # if the sink_path hadn't been found it was never registered ergo it is zero
        return 0
