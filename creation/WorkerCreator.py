from typing import List, Dict, Tuple
import datetime
import random
from datetime import timedelta
from creation.NameProvider import NameProvider
import json


class WorkerCreator:

    # "constants"
    job_boss = "boss"
    job_engineer = "engineer"
    job_warehouseman = "warehouseman"
    job_office = "paper pusher"     # :p -- aka office worker
    job_mechanic = "mechanic"
    job_electrician = "electrician"
    ability_economic = "Economics degree"
    ability_driving = "driving license"
    ability_engineering = "Engineering degree"
    ability_forklift = "forklift license"
    ability_office = "office training"
    ability_mechanic = "mechanical training"
    ability_electric = "electrical training"

    class Worker:
        id: str
        name: str
        job: str
        size: str
        age: int
        birthday: datetime
        skills: List[str]

        def __str__(self):
            return "{} with personal No \"{}\" is {} years old (birthday {}) and works as {} (skills: {})".format(
                self.name, self.id, self.age, self.birthday, self.job, self.skills
            )

        def to_worker_dict(self):
            return {
                "ID": self.id,
                "Name": self.name,
                "Job": self.job,
                "Size": self.size,
                "Age": self.age,
                "Birthday": self.birthday.strftime("%d.%m.%Y"),
                "Skills": self.skills
            }

    # fields
    __skill_pool: Dict[str, Tuple[List[str], List[str]]] = {
        job_boss: ([ability_economic, ability_driving], [ability_engineering]),
        job_engineer: ([ability_engineering, ability_driving], [ability_economic]),
        job_warehouseman: ([ability_driving], [ability_forklift, ability_office]),
        job_office: ([ability_office, ability_driving], ),
        job_mechanic: ([ability_mechanic, ability_driving], [ability_forklift]),
        job_electrician: ([ability_electric, ability_driving], [ability_office])
    }

    _workers: List[Worker] = []

    def __init__(self, worker_count: int):
        random.seed(42)     # ensure reproducibility
        start: int = 100000
        pool: List[str] = ["{:06d}".format(i) for i in range(start, start + worker_count)]
        random.shuffle(pool)
        for i in range(worker_count):
            current_worker = WorkerCreator.Worker()
            current_worker.id = pool[i]
            current_worker.name = NameProvider.get_name()
            current_worker.size = random.choice(["S", "M", "L", "XL"])
            current_worker.age = random.randrange(30, 55)
            current_worker.birthday = self.draw_birthday(current_worker.age)
            current_worker.job = self.draw_job()
            current_worker.skills = self.__skill_pool[current_worker.job][0]
            # draw a stick if the current worker has some "bonus" skills
            has_additional_skills = random.randrange(3) > 2
            if has_additional_skills:
                # append to the existing list of skill names
                current_worker.skills += self.__skill_pool[current_worker.job][1]
            self._workers.append(current_worker)

    def print_workers(self):
        print("Content of class")
        for worker in self._workers:
            print(worker)

    def _to_worker_dict_list(self):
        return [w.to_worker_dict() for w in self._workers]

    def to_json(self, sort_keys=True, indent=2) -> str:
        return json.dumps(self._to_worker_dict_list(), sort_keys=sort_keys, indent=indent)

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

    @staticmethod
    def draw_birthday(age: int) -> datetime:
        d: int = 182    # 365 / 2
        days = timedelta(days=random.randrange(-d, d))
        bd = datetime.date.today() + days
        try:
            bd = bd.replace(year=bd.year - age)
        except ValueError:
            bd = bd.replace()
        return bd


if __name__ == "__main__":
    # test the function
    wc = WorkerCreator(5)
    wc.print_workers()
