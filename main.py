"""
The main routine
"""
import shutil
import os

from creation import WorkerCreator, SectionCreator, Creator, FileModifier
from matcher.MatchingManager import MatchingManager
from evaluation.Differ import XmlDiffer

WORKER_FILE = "workers.json"
SECTION_FILE = "sections.json"


def generate_json(worker_count: int) -> None:
    """
    A wrapper function to wrap the json generation in one function call
    """
    wc = WorkerCreator.WorkerCreator(worker_count)
    result_file = open(WORKER_FILE, "w")
    result_file.write(wc.to_json())
    result_file.close()

    sc = SectionCreator.SectionCreator()
    result_file = open(SECTION_FILE, "w")
    result_file.write(sc.to_json())
    result_file.close()


def try_parse_int(to_parse: str) -> (bool, int):
    """
    Returns in the first boolean if the int in the string could be parsed and in the second the parsed int

    :param to_parse: the string which shall be parsed for an integer
    :return: a tuple containing the success-state of the parsing and the int if successful else 0
    """
    try:
        return True, int(to_parse)
    except ValueError:
        return False, 0


if __name__ == "__main__":
    default_xlsx_path = "data.xlsx"
    default_nested_dir = "sections"
    default_xml_path = "ref.xml"
    default_target_file = "test.xml"
    default_config_path = "config.toml"
    default_worker_cnt = 20
    print("Step one: creating environment:")
    previous_step_performed: bool = True
    shall_generate_base = input("Do you want me to generate data for you? (y/n)")
    if shall_generate_base == "y" or shall_generate_base == "Y":
        worker_count_input = input("How many workers shall be generated? (Default: {})".format(default_worker_cnt))
        not_default, worker_count = try_parse_int(worker_count_input)
        if not not_default:
            print("Did not understood the input. Using default value {}".format(default_worker_cnt))
            worker_count = default_worker_cnt
        # means to generate the json files from stock
        # worker_cnt = int(input("How many workers should be generated?"))
        generate_json(worker_count)
    elif shall_generate_base == "n" or shall_generate_base == "N":
        previous_step_performed = False
        # pass here to cover all other inputs with the else branch
        pass
    else:
        raise AttributeError("Could not map {} to a 'y' or 'n'".format(shall_generate_base))

    # print an empty line for separation
    print()
    print("Step two: Generating mock data from JSON")
    if previous_step_performed:
        shall_generate_mock = input("Shall I use the existing data to generate mocking data? (y/n)")
    else:
        shall_generate_mock = "n"
    if shall_generate_mock == "y" or shall_generate_mock == "Y":
        c = Creator.Creator(path_to_workers=WORKER_FILE, path_to_sections=SECTION_FILE)
        c.create_xlsx(".", default_xlsx_path, default_nested_dir)
        c.create_xml(default_xml_path)
        c.create_config_file(default_config_path)
    elif shall_generate_mock == "n" or shall_generate_mock == "N":
        previous_step_performed = False
        # pass here to cover all other inputs with the else branch
        pass
    else:
        raise AttributeError("Could not map %s to a 'y' or 'n'".format(shall_generate_base))

    print()
    print("Step three: training")
    # TODO: get a deviating xlsx-path here?
    # m = XmlXlsxMatcher("config.toml", default_xlsx_path)
    # m.test_table_reading()
    manager = MatchingManager(default_config_path, "log/result.log")
    manager.train(default_xml_path, default_xlsx_path, "{}/".format(default_nested_dir))
    manager.dump_classifier_matrix("table")
    manager.create_build_environment("template/template.xml")
    node_count = manager.generate(default_target_file)
    print("Created '{}' with {} nodes".format(default_target_file, node_count))

    print()
    print("Step four: comparing original XML with generated XML")
    differ = XmlDiffer("log/compare.log", default_config_path)
    differ.compare(default_xml_path, default_target_file)

    print()
    print("Step five: temper with some data in the xlsx")
    tempered_xml = "updated.xml"
    # will override the old data.xlsx file -> copy it to a new name as backup
    print("Before updating the xlsx-file storing the old file as data.old.xlsx")
    shutil.copy(default_xlsx_path, "data.old.xlsx")
    FileModifier.XlsxModifier.update_worker_xlsx(default_worker_cnt, default_xlsx_path)
    manager.generate(tempered_xml)
    differ = XmlDiffer("log/compare_of_updated.log", default_config_path)
    differ.compare(default_xml_path, tempered_xml)

    print()
    print("Step six: add an additional worker")
    print("Creating backup of last xlsx-file under data.updated.xlsx")
    shutil.copy(default_xlsx_path, "data.updated.xlsx")
    FileModifier.XlsxModifier.add_worker_to_xlsx(default_worker_cnt, default_xlsx_path)
    manager.generate("extended.xml")
    differ = XmlDiffer("log/compare_of_extended.log", default_config_path)
    # test against the updated XML as the xlsx was never reset from the update
    differ.compare(tempered_xml, "extended.xml")

    print(os.linesep + "Done!")
