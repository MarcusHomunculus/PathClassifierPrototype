"""
The main routine
"""

from creation import WorkerCreator, SectionCreator, Creator
from matcher.XmlXlsxMatcher import XmlXlsxMatcher
from matcher.MatchingManager import MatchingManager

workerFile = "workers.json"
sectionFile = "sections.json"


def generate_json(worker_count: int) -> None:
    """
    A wrapper function to wrap the json generation in one function call
    """
    wc = WorkerCreator.WorkerCreator(worker_count)
    result_file = open(workerFile, "w")
    result_file.write(wc.to_json())
    result_file.close()

    sc = SectionCreator.SectionCreator()
    result_file = open(sectionFile, "w")
    result_file.write(sc.to_json())
    result_file.close()


if __name__ == "__main__":
    default_xlsx_path = "data.xlsx"
    print("Step one: creating environment:")
    # shall_generate_base = input("Do you want me to generate data for you? (y/n)")
    shall_generate_base = "y"
    if shall_generate_base == "y" or shall_generate_base == "Y":
        # means to generate the json files from stock
        # worker_cnt = int(input("How many workers should be generated?"))
        worker_cnt = 10
        generate_json(worker_cnt)
    elif shall_generate_base == "n" or shall_generate_base == "N":
        # pass here to cover all other inputs with the else branch
        pass
    else:
        raise AttributeError("Could not map %s to a 'y' or 'n'".format(shall_generate_base))

    print("Step two: Generating mock data from JSON")
    # shall_generate_mock = input("Shall I use the existing data to generate mocking data? (y/n)")
    shall_generate_mock = "n"
    if shall_generate_mock == "y" or shall_generate_mock == "Y":
        c = Creator.Creator(path_to_workers=workerFile, path_to_sections=sectionFile)
        c.create_xlsx(".", default_xlsx_path, "sections")
        c.create_xml("ref.xml")
        c.create_config_file("config.toml")
    elif shall_generate_mock == "n" or shall_generate_mock == "N":
        # pass here to cover all other inputs with the else branch
        pass
    else:
        raise AttributeError("Could not map %s to a 'y' or 'n'".format(shall_generate_base))

    print("Step three: training")
    # TODO: get a deviating xlsx-path here?
    # m = XmlXlsxMatcher("config.toml", default_xlsx_path)
    # m.test_table_reading()
    manager = MatchingManager("config.toml", default_xlsx_path, "nested/")
    manager.match_in_xlsx_sink([])

    print("Done!")
