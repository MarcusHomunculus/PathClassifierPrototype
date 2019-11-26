"""
The main routine
"""

from creation import WorkerCreator, SectionCreator

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


print("Step one: creating environment:")
shall_generate_base = input("Do you want me to generate data for you? (y/n)")
if shall_generate_base == "y" or shall_generate_base == "Y":
    # means to generate the json files from stock
    generate_json(10)

elif shall_generate_base == "n" or shall_generate_base == "N":
    # pass here to cover all other inputs with the else branch
    pass
else:
    raise AttributeError("Could not map %s to a 'y' or 'n'".format(shall_generate_base))

print("Done!")
