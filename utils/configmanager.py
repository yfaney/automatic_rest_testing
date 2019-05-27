import sys

if sys.version_info[0] < 3:
    # Python 2 uses this module
    from ConfigParser import ConfigParser
else:
    # Python 3 uses this module
    from configparser import ConfigParser


class ConfigManager:
    """
    Manages config file contents
    """

    def __init__(self, filepath):
        """
        Creates ConfigManager instance.
        :param filepath: File path
        """
        self.filepath = filepath
        self.config = ConfigParser()
        self.config.optionxform = str
        self.config.read(filepath)

    def parse(self):
        # type: () -> dict
        """
        Parses the contents of config file into a dictionary.
        :return: The parsed config information
        """
        info = {}
        for section in self.config.sections():
            cfg_item = {}
            for item in self.config.items(section):
                cfg_item[item[0]] = item[1]
            info[section] = cfg_item
        return info
