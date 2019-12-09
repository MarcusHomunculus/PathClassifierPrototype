import toml


class XmlXlsxMatcher:

    __config = {}

    def __init__(self, path_to_config: str):
        self.__read_config(path_to_config)

    def __read_config(self, path_to_file: str) -> None:
        config = {}
        with open(path_to_file, "r", encoding="utf-8") as c:
            config.update(toml.load(c))
        self.__config = config
