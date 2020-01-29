import datetime

from creation.FileSystem import create_directories_for


class DiffLogger:

    __sink_file: str
    __name: str
    __error_count: int
    __first: str
    __second: str

    def __init__(self, name: str, sink_file: str):
        """
        Created a small custom logger without high functionality for higher customizability and proper output (no
        prioritization which messes up the output with other parts of the program)

        :param name: the name of the logger
        :param sink_file: the file path were to write the errors to
        """
        self.__name = name
        self.__sink_file = sink_file
        create_directories_for(self.__sink_file)
        self.__error_count = 0

    def start(self, first_file: str, second_file: str) -> None:
        """
        Starts the logging process by creating the log file and writing the summary of the task to the console

        :param first_file: the name of the first file
        :param second_file: the name of the second file
        """
        self.__first = first_file
        self.__second = second_file
        title = "Comparision of {} vs {}:".format(self.__first, self.__second)
        print(title, file=open(self.__sink_file, "w"))
        print("Starting comparision of {} with {}. Writing results to {}".format(self.__first, self.__second,
                                                                                 self.__sink_file))

    def error(self, message: str) -> None:
        """
        Records an error and writes it to the log file and the console

        :param message: the message to record
        """
        # write to the console
        print("{} : {}".format(self.__name, message))
        # and to the log file
        print("{} : {}".format(datetime.datetime.now().time(), message), file=open(self.__sink_file, "a"))
        self.__error_count += 1

    def finalize(self) -> None:
        """
        Completes the logging process by writing the result to the file and the console
        """
        print("Comparision completed: found {} error".format(self.__error_count))
        print("Completed with {} errors".format(self.__error_count), file=open(self.__sink_file, "a"))
