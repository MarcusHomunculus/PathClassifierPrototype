import json
import random

from creation.WorkerCreator import WorkerCreator


class XlsxModifier:

    @staticmethod
    def update_worker_json_to(source_path: str, target_path: str, indent_target: int = 2) -> None:
        """
        Updates the age and the size of 2 randomly picked workers from the given worker-JSON-file and writes the
        modifications to the new file

        :param source_path: the JSON file to read the workers from
        :param target_path: the JSON file to write the updated workers (and the rest) to
        :param indent_target: what indentation to use for the target file
        """
        with open(source_path, "r") as f:
            data_tree = json.load(f)
            first_victim = random.randint(0, len(data_tree) - 1)
            new_age = 30
            print("Changing the age of {} to {}".format(data_tree[first_victim]["Name"], new_age))
            data_tree[first_victim]["Age"] = new_age
            new_birthday = WorkerCreator.draw_birthday(new_age)
            data_tree[first_victim]["Birthday"] = WorkerCreator.format_date(new_birthday)
            second_victim = random.randint(0, len(data_tree) - 1)
            new_size = "XS"
            print("Changing size of {} to {}".format(data_tree[second_victim]["Name"], new_size))
            data_tree[second_victim]["Size"] = new_size
            with open(target_path, "w") as s:
                json.dump(data_tree, s, sort_keys=False, indent=indent_target)
