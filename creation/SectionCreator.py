from typing import List, Dict
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
    TEAM_KEY = "Teams"

    __section_data = {
        section_name_h_r: ([WorkerCreator.ability_office],  # required skills
                           [],                              # optional skills
                           payment_stage_1,                 # payment level
                           1,                               # worker_fraction
                           [                                # teams
                               ("Accounting", 0.8), ("Taxing", 0.2)
                           ]),
        section_name_logistic: ([],
                                [WorkerCreator.ability_forklift],
                                payment_stage_0,
                                1.5,
                                [
                                    ("Racking", 0.5), ("Forklift", 0.5)
                                ]),
        section_name_r_d: ([WorkerCreator.ability_engineering],
                           [],
                           payment_stage_3,
                           1,
                           [
                               ("Manufacturing", 0.3), ("Product development", 0.5), ("process planning", 0.2)
                           ]),
        section_name_prod: ([],
                            [WorkerCreator.ability_electric, WorkerCreator.ability_mechanic],
                            payment_stage_1,
                            4.5,
                            [
                                ("Electric installation", 0.3), ("Casing production", 0.4), ("QS", 0.3)
                            ]),
        section_name_management: ([WorkerCreator.ability_economic],
                                  [WorkerCreator.ability_office],
                                  payment_stage_3,
                                  0.5,
                                  [
                                      ("Upper management", 0.1), ("Lower management", 0.4), ("Secretary offices", 0.5)
                                  ]),
        section_name_marketing: ([WorkerCreator.ability_economic],
                                 [],
                                 payment_stage_2,
                                 0.5,
                                 [
                                     ("Advertisement", 0.5), ("Customer management", 0.5)
                                 ]),
        section_name_field: ([WorkerCreator.ability_driving],
                             [WorkerCreator.ability_mechanic, WorkerCreator.ability_electric,
                             WorkerCreator.ability_engineering],
                             payment_stage_3,
                             1,
                             [
                                 ("Field crew", 1.0)
                             ])
    }

    class Section:
        name: str
        abilities: List[str]
        payment_level: int
        worker_fraction: float  # normalized to 10 workers
        teams: Dict[str, float]

        def to_dict(self):
            return {
                "Name": self.name,
                "Abilities": self.abilities,
                "PaymentStage": self.payment_level,
                "NormalizedWorkerCount": self.worker_fraction,
                SectionCreator.TEAM_KEY: self.teams
            }

    _sections: List[Section] = []

    def __init__(self):
        for section in self.__section_data:
            current_section = SectionCreator.Section()
            current_section.name = section
            current_section.abilities = self.__section_data[section][0] + self.__section_data[section][1]
            current_section.payment_level = self.__section_data[section][2]
            current_section.worker_fraction = self.__section_data[section][3]
            current_section.teams = {}
            for team in self.__section_data[section][4]:
                # a list of tuples
                current_section.teams[team[0]] = team[1]
            self._sections.append(current_section)

    def to_json(self, sort_keys=False, indent=2) -> str:
        return json.dumps([s.to_dict() for s in self._sections], sort_keys=sort_keys, indent=indent)
