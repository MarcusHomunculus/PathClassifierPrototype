import random
from openpyxl import load_workbook

from creation.WorkerCreator import WorkerCreator


class XlsxModifier:

    first_row = 7

    @staticmethod
    def update_worker_xlsx(worker_cnt: int, source_file: str) -> None:
        """
        Changes the age of a randomly picked worker and the size of another randomly picked worker

        :param worker_cnt: the number of workers to pick from
        :param source_file: the file to modify
        """
        print("Assuming C{} in Workers as first entry in name column".format(XlsxModifier.first_row))
        print("Assuming columns E, F & G represent the Size, the Age & the Birthday in Workers")
        wb = load_workbook(source_file)
        worker_sheet = wb["Workers"]
        first_victim = random.randint(0, worker_cnt - 1)
        new_age = 67
        print("Changing the age of {} to {}".format(worker_sheet["C{}".format(
            XlsxModifier.first_row + first_victim)].value, new_age))
        worker_sheet["F{}".format(XlsxModifier.first_row + first_victim)].value = str(new_age)
        new_birthday = WorkerCreator.draw_birthday(new_age)
        worker_sheet["G{}".format(XlsxModifier.first_row + first_victim)].value = WorkerCreator.format_date(new_birthday)
        second_victim = random.randint(0, worker_cnt - 1)
        new_size = "XS"
        print("Changing size of {} to {}. This should have no impact on the final XML-file".format(
            worker_sheet["C{}".format(XlsxModifier.first_row + second_victim)].value, new_size))
        worker_sheet["E{}".format(XlsxModifier.first_row + second_victim)].value = new_size
        wb.save(source_file)
