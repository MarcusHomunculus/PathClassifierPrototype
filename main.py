"""
The main routine
"""

from creation import WorkerCreator


wc = WorkerCreator.WorkerCreator(3)
result_file = open("workers.json", "w")
result_file.write(wc.to_json())
result_file.close()


