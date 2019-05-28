from typing import List
import json
# to pull the string from there
from creation.WorkerCreator import WorkerCreator


class SectionCreator:

    # "Constants"
    section_name_h_r = "Human Resource"
    section_name_logistic = "Logistics"
    section_name_r_d = "Research and Development"
    section_name_prod = "Production"
    section_name_management = "Management and Finance"
    section_name_marketing = "Marketing"
    section_name_field = "Field crew"
    payment_stage_0 = 2000
    payment_stage_1 = 3000
    payment_stage_2 = 4000
    payment_stage_3 = 5000

    __section_data = {
        section_name_h_r: ([WorkerCreator.ability_office],  # required skills
                           [],                              # optional skills
                           payment_stage_1,                 # payment level
                           1),                              # worker_fraction
        section_name_logistic: ([],
                                [WorkerCreator.ability_forklift],
                                payment_stage_0,
                                1.5),
        section_name_r_d: ([WorkerCreator.ability_engineering],
                           [],
                           payment_stage_3,
                           1),
        section_name_prod: ([],
                            [WorkerCreator.ability_electric, WorkerCreator.ability_mechanic],
                            payment_stage_1,
                            4.5),
        section_name_management: ([WorkerCreator.ability_economic],
                                  [WorkerCreator.ability_office],
                                  payment_stage_3,
                                  0.5),
        section_name_marketing: ([WorkerCreator.ability_economic],
                                 [],
                                 payment_stage_2,
                                 0.5),
        section_name_field: ([WorkerCreator.ability_driving],
                             [WorkerCreator.ability_mechanic, WorkerCreator.ability_electric,
                             WorkerCreator.ability_engineering],
                             payment_stage_3,
                             1)
    }

    class Section:
        name: str
        abilities: List[str]
        payment_level: int
        worker_fraction: float  # normalized to 10 workers

        def to_dict(self):
            return {
                "Name": self.name,
                "Abilities": self.abilities,
                "PaymentStage": str(self.payment_level),
                "NormalizedWorkerCount": str(self.worker_fraction)
            }

    _sections: List[Section] = []

    def __init__(self):
        for section in self.__section_data:
            current_section = SectionCreator.Section()
            current_section.name = section
            current_section.abilities = self.__section_data[section][0] + self.__section_data[section][1]
            current_section.payment_level = self.__section_data[section][2]
            current_section.worker_fraction = self.__section_data[section][3]
            self._sections.append(current_section)

    def to_json(self, sort_keys=False, indent=2) -> str:
        return json.dumps([s.to_dict() for s in self._sections], sort_keys=sort_keys, indent=indent)
