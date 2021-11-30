import praw
from datetime import datetime
import os

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
        year=curr_ts.year, month=curr_ts.month, day=curr_ts.day, hour=curr_ts.hour, minute=curr_ts.minute, second=curr_ts.second, micro=curr_ts.microsecond)
    return out_string


def gen_reddit(login):
    reddit_handle = praw.Reddit(client_id=login.get("client_id"),
                                client_secret=login.get("client_secret"),
                                user_agent=login.get("user_agent"),
                                username=login.get("username"),
                                password=login.get("password")
                                )
    print("reddit handle has been generated")
    return reddit_handle