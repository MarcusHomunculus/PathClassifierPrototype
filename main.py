"""
The main routine
"""

from creation import WorkerCreator, SectionCreator

workerFile = "workers.json"
sectionFile = "sections.json"


def generate_json() -> None:
    """
    A wrapper function to wrap the json generation in one function call
    """
    wc = WorkerCreator.WorkerCreator(3)
    result_file = open(workerFile, "w")
    result_file.write(wc.to_json())
    result_file.close()

    sc = SectionCreator.SectionCreator()
    result_file = open(sectionFile, "w")
    result_file.write(sc.to_json())
    result_file.close()


print("Step one: creating environment:")
generateBase = input("Do you want me to generate data for you? (y/n)")
if generateBase == "y" or generateBase == "Y":
    # means to generate the json files from stock
    generate_json()
elif generateBase == "n" or generateBase == "N":
    # pass here to cover all other inputs with the else branch
    pass
else:
    raise AttributeError("Could not map %s to a 'y' or 'n'".format(generateBase))

# TODO: continue here

print("Done!")
