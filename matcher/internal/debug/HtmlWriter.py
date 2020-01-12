from typing import List, Tuple
import html

class HtmlWriter:

    _raw_data: List[Tuple[str, List[str, int]]]

    def __init__(self, raw_data: List[Tuple[str, List[str, int]]]):
        """
        The constructor

        :param raw_data: the data to construct the html data from
        """
        self._raw_data = raw_data

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
        # now for the body
        row_template = get_template("table_row")
        cell_template = get_template("match_cell")
        table_body = ""
        for row in self.__mat:
            current_row = row_template.replace("[%SOURCE_PATH%]", row.get_key())
            matrix_row_str = ""
            for bin_count in row.get_bins():
                matrix_row_str += cell_template.replace("[%COUNT%]", str(bin_count)) + "\n"
            table_body += current_row.replace("[%MATCHES%]", matrix_row_str)
        content = content.replace("[%BODY%]", table_body)
        # write to file
        if not target_path.endswith(".html"):
            target_path += ".html"
        print("Dumping classifier matrix as HTML into " + target_path)
        with open(target_path, "w+") as sink_file:
            sink_file.write(content)