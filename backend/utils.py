import logging
import os
from datetime import datetime

import praw
import asyncpraw

porn_subreddits = [
    "gonewild",
    "AsiansGoneWild",
    "realasians",
    "xsmallgirls",
]
tech_subrredits = [
    "MachineLearning",
    "dataisbeautiful",
    "hardware",
    "nvidia",
]

comm_subrredits = [
    "news",
]

japan_subreddits = [
    "japanlife",
    "japan",
    "japanpics",
]


def setup_logging(self, log_level=logging.DEBUG):
    FORMAT = "%(asctime)s %(levelname)7s %(filename)20s:%(lineno)4s - %(name)15s.%(funcName)16s() %(message)s"

    log_dir = "logs/"
    log_file = log_dir + "{name}.log".format(name=type(self).__name__)
    create_directory(log_dir)
    if not os.path.exists(log_file):
        with open(log_file, "w+") as f:
            f.write(
                "-------------- LOG FILE FOR {name} --------------\n".format(
                    name=type(self).__name__
                )
            )

    self.logger = logging.getLogger(type(self).__name__)
    if not self.logger.hasHandlers():
        self.logger.setLevel(log_level)

        file_handler = logging.FileHandler(log_file, encoding=None, delay=False)
        stream_handler = logging.StreamHandler()

        file_handler.setLevel(logging.INFO)
        stream_handler.setLevel(logging.DEBUG)

        file_format = logging.Formatter(FORMAT)
        stream_format = logging.Formatter(FORMAT)

        file_handler.setFormatter(file_format)
        stream_handler.setFormatter(stream_format)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)

    return


def create_directory(directory):
    """
    :param dir: directory name to be created
    :return: True or False
    """
    if not os.path.exists(directory):
        print("[INFO] Creating the following directory: " + directory)
        return os.makedirs(directory)
    else:
        return False


def timestamp():
    curr_ts = datetime.now()
    out_string = "{year:04d}{month:02d}{day:02d}{hour:02d}{minute:02d}{second:02d}{micro:06d}".format(
        year=curr_ts.year,
        month=curr_ts.month,
        day=curr_ts.day,
        hour=curr_ts.hour,
        minute=curr_ts.minute,
        second=curr_ts.second,
        micro=curr_ts.microsecond,
    )
    return out_string


def gen_reddit(login):
    reddit_handle = praw.Reddit(
        client_id=login.get("client_id"),
        client_secret=login.get("client_secret"),
        user_agent=login.get("user_agent"),
        username=login.get("username"),
        password=login.get("password"),
    )
    print("reddit handle has been generated")
    return reddit_handle
