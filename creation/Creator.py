

class Creator:
    """
    The class which creates the files which the learning algorithm can use for
    training
    """

    def __init__(self, src: str):
        """
        The constructor

        :param src: the path to the file which contains the raw data to serialize into excel and xml
        """
        pass

    def build_env(self):
        pass

    def _build_xlsx(self):
        pass

    def _build_xml(self):
        pass


if __name__ == "__main__":
    c = Creator()
    c.build_env()
