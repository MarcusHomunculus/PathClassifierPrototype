import toml


class XmlXlsxMatcher:

    FORWARDING_KEY = "forwarding"

    __config = {}

    def __init__(self, path_to_config: str):
        # TODO: doc me
        self.__read_config(path_to_config)

    def __read_config(self, path_to_file: str) -> None:
        # TODO: write some nice docu here
        config = {}
        with open(path_to_file, "r", encoding="utf-8") as c:
            config.update(toml.load(c))
        self.__config = config

    def _axis_is_forwarding(self, name: str) -> bool:
        # TODO: doc me
        # TODO: debug me: what kind of data is behind the keyword?
        if XmlXlsxMatcher.FORWARDING_KEY not in self.__config:
            return False    # no forwarding specified
        if not self.__config[XmlXlsxMatcher.FORWARDING_KEY].keys():
            return False
        return True

