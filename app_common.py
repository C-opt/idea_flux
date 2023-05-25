import logging

from praw import Reddit

from backend.sql import SQL
from backend.utils import setup_logging


class SystemVariables:
    """
    Class storing important system variables
    """

    def __init__(self):
        self.logger = None
        setup_logging(self, logging.INFO)
        self.variables = {}

    def __getitem__(self, key):
        return self.variables[key]

    def __setitem__(self, key, value):
        if key == "sql_handle":
            assert type(value) == SQL
        elif key == "reddit_handle":
            assert type(value) == Reddit
        self.logger.info("Insert item in system variables: " + key)
        # self.logger.info(key)
        self.variables[key] = value

    def __delitem__(self, key):
        del self.variables[key]

    def __len__(self):
        return len(self.variables)

    def __contains__(self, key):
        return key in self.variables

    def keys(self):
        return self.variables.keys()

    def values(self):
        return self.variables.values()

    def items(self):
        return self.variables.items()
