from typing import List
# to pull the string from there
from creation.WorkerCreator import WorkerCreator


class SectionCreator:

    _section_names = {
        "Human Resource": ([WorkerCreator.ability_office], ),
        "Logistics": ([], [WorkerCreator.ability_forklift]),
        "Research and Development": ([WorkerCreator.ability_engineering]),
        "Production": ([], [WorkerCreator.ability_electric], [WorkerCreator.ability_mechanic]),
        "Management and Finance": ([WorkerCreator.ability_economic], [WorkerCreator.ability_office]),
        "Marketing": ([WorkerCreator.ability_economic]),
        "Field crew": ([WorkerCreator.ability_driving],
                       [WorkerCreator.ability_mechanic, WorkerCreator.ability_electric,
                        WorkerCreator.ability_engineering])
    }

    class Section:
        name: str
        required_abilities: List[str]
        budget: int
        income: int
        size: int

    _sections: List[Section] = []

    def __init__(self):
        pass

    def to_json(self) -> str:
        pass
