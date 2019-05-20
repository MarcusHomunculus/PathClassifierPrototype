from .NameList import NameList, AttrList
from typing import List, Dict, Tuple
import datetime
import random
from datetime import timedelta


class WorkerCreator:

    job_boss = "boss"
    job_engineer = "engineer"
    job_warehouseman = "warehouseman"
    job_office = "human resource"
    job_mechanic = "mechanic"
    job_electrician = "electrician"
    ability_economic = "Economics degree"
    ability_driving = "driving license"
    ability_engineering = "Engineering degree"
    ability_forklift = "forklift license"
    ability_office = "office training"
    ability_mechanic = "mechanical training"
    ability_electric = "electrical training"

    __skill_pool: Dict[str, Tuple[List[str], List[str]]] = {
        job_boss: ([ability_economic, ability_driving], [ability_engineering]),
        job_engineer: ([ability_engineering, ability_driving], [ability_economic]),
        job_warehouseman: ([ability_driving], [ability_forklift, ability_office]),
        job_office: ([ability_office, ability_driving], ),
        job_mechanic: ([ability_mechanic, ability_driving], [ability_forklift]),
        job_electrician: ([ability_electric, ability_driving], [ability_office])
    }

    from json import JSONEncoder

    class Worker(JSONEncoder):
        id: str
        name: str
        job: str
        size: str
        age: int
        birthday: datetime
        skills: List[str]

    def __init__(self, worker_count: int):
        random.seed(42)     # ensure reproducibility
        start: int = 100000
        pre_pool = ["{:06d}".format(i) for i in range(start, start + worker_count)]
        pool: List[str] = random.shuffle(pre_pool)
        for i in range(worker_count):
            current_worker = WorkerCreator.Worker()
            current_worker.id = pool(i)
            current_worker.name = "{} {}".format(AttrList[random.randrange(len(AttrList))],
                                                 NameList[random.randrange(len(NameList))])
            current_worker.size = random.choice(["S", "M", "L", "XL"])
            current_worker.age = random.randrange(30, 55)
            d: int = 182    # 365 / 2
            days = timedelta(days=random.randrange(-d, d))
            current_worker.birthday = datetime.date.today() + days
            current_worker.job = self.draw_job()
            current_worker.skills = self.__skill_pool[current_worker.job][0]
            # draw a stick if the current worker has some "bonus" skills
            has_additional_skills = random.randrange(3) > 2
            if has_additional_skills:
                # append to the existing list of skill names
                current_worker.skills += self.__skill_pool[current_worker.job][1]

    @staticmethod
    def draw_job() -> str:
        rand_for_job = random.gauss(0, 0.4)
        # bosses and engineers are quite rare so pick them from the "corners" of the bell curve
        if rand_for_job < -0.5:
            return  WorkerCreator.job_engineer
        if rand_for_job > 0.7:
            return WorkerCreator.job_boss
        # just pick randomly -> no preference
        worker_prob = random.uniform(0.0, 1.0)
        if worker_prob < 0.25:
            return WorkerCreator.job_warehouseman
        if worker_prob < 0.5:
            return WorkerCreator.job_office
        if worker_prob < 0.75:
            return WorkerCreator.job_mechanic
        else:
            return WorkerCreator.job_electrician
