import argparse
import datetime as dt
import io
import logging
import os
import re
import time

import numpy as np
import pandas as pd
import requests
import yaml
from pandas.core.frame import DataFrame
from PIL import Image

# synchronous version of PRAW
from praw import Reddit
from praw.models import Comment, Submission, Subreddit

# async version of PRAW
# from asyncpraw import Reddit
# from asyncpraw.models import Comment, Submission, Subreddit

from backend.sql import SQL
from backend.utils import create_directory, gen_reddit, setup_logging


class IdeaFluxSubreddit:
    """_summary_"""

    def __init__(self, reddit_handle: Reddit, subreddit_name: str):
        self.logger = None
        setup_logging(self)
        self.subreddit_handle = reddit_handle.subreddit(subreddit_name)
        self.logger.debug(type(self.subreddit_handle))

        self.subreddit_name = self.subreddit_handle.name
        self.subreddit_display_name = self.subreddit_handle.display_name
        self.subreddit_submissions = list()

    def load_submissions(
        self, mode="hot", limit=10, ignore_subs=list()
    ) -> list[Submission]:
        """load submissions

        Args:
            mode (str, optional): _description_. Defaults to "hot".
            limit (int, optional): _description_. Defaults to 10.
            ignore_subs (list, optional): _description_. Defaults to [].

        Returns:
            list[Submission]: _description_
        """
        submissions = list()
        if mode == "hot":
            for submission in self.subreddit_handle.hot(limit=limit):
                submissions.append(submission)

        if mode == "rising":
            for submission in self.subreddit_handle.rising(limit=limit):
                submissions.append(submission)

        if mode == "random_rising":
            for submission in self.subreddit_handle.random_rising(limit=limit):
                submissions.append(submission)

        for s in submissions:
            if s.id not in ignore_subs:
                self.subreddit_submissions.append(s)
        return submissions

    def submission_dict_init(
        self,
    ) -> dict:
        """Initiate submission dictionary"""
        submission_dict = dict()

        submission_dict.update({"submission_id": list()})
        submission_dict.update({"comments_num": list()})
        submission_dict.update({"score": list()})
        submission_dict.update({"subreddit_id": list()})
        submission_dict.update({"subreddit_display_name": list()})
        submission_dict.update({"title": list()})
        submission_dict.update({"created": list()})
        submission_dict.update({"url": list()})

        submission_dict.update({"body": list()})

        # submission_dict.update({"user_engagement":list()})

        return submission_dict

    def submissions2df(
        self,
    ) -> pd.DataFrame:
        """transform submissions into dataframes"""
        submission_dict = self.submission_dict_init()
        for submission in self.subreddit_submissions:
            # self.logger.info(vars(submission))
            submission_dict.get("title").append(submission.title)
            submission_dict.get("score").append(submission.score)
            submission_dict.get("submission_id").append(submission.id)
            submission_dict.get("url").append(
                "https://reddit.com" + submission.permalink
            )
            submission_dict.get("comments_num").append(submission.num_comments)
            submission_dict.get("created").append(submission.created)
            submission_dict.get("body").append(submission.selftext)
            submission_dict.get("subreddit_id").append(self.subreddit_name)
            submission_dict.get("subreddit_display_name").append(
                self.subreddit_display_name
            )

        sub_df = pd.DataFrame(submission_dict)
        return sub_df


class IdeaFluxSubmission:
    """Class for formatting the submission"""

    def __init__(
        self,
        submission_id: str,
        reddit_handle: Reddit,
    ):
        self.logger = None
        setup_logging(self)
        self.submission_handle = reddit_handle.submission(submission_id)
        self.logger.info("sub id: {a}".format(a=submission_id))
        self.submission_comments = list()
        self.submission_id = submission_id

    def comment_dict_init(
        self,
    ) -> dict:
        """_summary_

        Returns:
            dict: _description_
        """
        comm_dict = dict()
        comm_dict.update({"comment_id": list()})
        comm_dict.update({"parent_id": list()})
        comm_dict.update({"submission_id": list()})
        comm_dict.update({"body": list()})
        # comm_dict.update({"weight":list()})
        # comm_dict.update({"type":list()})

        return comm_dict

    def comments2df(
        self,
    ) -> pd.DataFrame:
        """Transforms comments to pandas.DataFrame

        Returns:
            pd.DataFrame: _description_
        """
        comm_dict = self.comment_dict_init()
        TEXT_CLEANING_RE = "@\S+|https?:\S+|http?:\S|[^A-Za-z0-9]+"
        EMOJI_PATTERN = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+",
            flags=re.UNICODE,
        )

        for comment in self.submission_comments:
            # self.logger.info(20*"#")
            # self.logger.info("Parent ID: ", comment.parent())
            # self.logger.info("Comment ID: ", comment.id)
            # self.logger.info(comment.body)

            comm_dict.get("parent_id").append(comment.parent().id)
            comm_dict.get("comment_id").append(comment.id)
            comm_dict.get("submission_id").append(self.submission_id)

            # text = re.sub(TEXT_CLEANING_RE, " ", str(comment.body).lower()).strip()
            text = EMOJI_PATTERN.sub(" ", str(comment.body))
            text = text.strip()
            comm_dict.get("body").append(text)
            # comm_dict.get("type").append("Undirected")
            # comm_dict.get("weight").append(1)

        comm_df = pd.DataFrame(comm_dict)
        return comm_df

    def load_comments(self, max_comm=200) -> list:
        """load comments of submission handle

        Args:
            max_comm (int, optional): max number of comments to be loaded. Defaults to 200.

        Returns:
            list: list of comments
        """
        self.logger.info("comments.replace_more()  ...")
        t0 = time.time()
        while True:
            try:
                self.submission_handle.comments.replace_more(limit=max_comm)
                break
            except Exception as e:
                self.logger.info(
                    "handling comments.replace_more(limit=max_comm): {e}".format(e=e)
                )
                time.sleep(1.0)
            self.logger.info(
                "#comms processed: {a} of {b}".format(
                    a=len(self.submission_handle.comments.list()), b=2
                )
            )
        t1 = time.time()
        self.logger.info(
            "comments.replace_more() took {comms_replace_time:4.2f} seconds".format(
                comms_replace_time=t1 - t0
            )
        )

        self.logger.info("comments.list() ...")
        t0 = time.time()
        comms_list = self.submission_handle.comments.list()

        t1 = time.time()
        self.logger.info(
            "{num_comms} comments in {comms_list_time:4.2f} seconds".format(
                num_comms=len(comms_list), comms_list_time=t1 - t0
            )
        )
        for c in comms_list:
            self.submission_comments.append(c)
        return comms_list


# https://www.postgresqltutorial.com/postgresql-python/insert/
# https://stackoverflow.com/questions/23103962/how-to-write-dataframe-to-postgres-table


class DataScraper:
    """Data scraper class. It mines information from reddit."""

    def __init__(self, **kwargs):
        self.logger = None
        setup_logging(self)
        self.subreddits_name_list: list = kwargs.get("subreddits_name_list")
        self.reddit_handle: Reddit = kwargs.get("reddit_handle")

        self.sql_handle: SQL = kwargs.get("sql_handle")
        assert type(self.sql_handle) is SQL
        assert type(self.reddit_handle) is Reddit
        # host = kwargs.get("host")
        # database = kwargs.get("database")
        # user = kwargs.get("user")
        # password = kwargs.get("password")

    def subreddit_routine(self, max_num_submissions=10):
        """Subreddit routine method. It loads submissions from a list of subreddits.

        Args:
            max_num_submissions (int, optional): maximum number of submissions per subreddit. Defaults to 10.
        """
        already_processed_submission_ids = self.sql_handle.get_column_from_table(
            "submissions", "submission_id"
        )
        for subreddit_name in self.subreddits_name_list:
            self.logger.info(subreddit_name)
            subreddit_handle = IdeaFluxSubreddit(
                subreddit_name=subreddit_name, reddit_handle=self.reddit_handle
            )

            subreddit_handle.load_submissions(
                limit=max_num_submissions, ignore_subs=already_processed_submission_ids
            )

            submissions_df = subreddit_handle.submissions2df()
            _ts = submissions_df.get("created").apply(self.get_date)
            submissions_df = submissions_df.assign(created=_ts)
            submissions_df = submissions_df.sort_values(
                by="comments_num", ascending=False
            )
            self.logger.debug(submissions_df)
            self.logger.info("insert dataframes into DB")
            self.sql_handle.execute_values(submissions_df, "submissions")

    def submission_routine(self, max_num_comments=100):
        """Submission routine method. It loads comments from submissions that haven't mined yet.

        Args:
            max_num_comments (int, optional): maximum number of comments to be loaded. Defaults to 100.
        """
        # get submission id that has been created in less than 2 days, and has more than 0 comments
        submission_ids = self.sql_handle.get_column_from_table(
            "submissions",
            "submission_id",
            " WHERE comments_num > 0 AND created > now() - interval '2 day';",
        )
        # get submission ids that have already been loaded into the DB
        already_processed_submission_ids = self.sql_handle.get_column_from_table(
            "reddit_comments",
            "submission_id",
        )

        # filter out submission ids that already have been loaded
        tbproc_sub_ids = list(
            set(submission_ids) - set(already_processed_submission_ids)
        )

        # start loading the comments
        for submission_id in tbproc_sub_ids:
            self.logger.info(submission_id)
            submission_handle = IdeaFluxSubmission(
                submission_id=submission_id, reddit_handle=self.reddit_handle
            )
            # if submission is stickied or NSFW, then skip it
            if (
                submission_handle.submission_handle.stickied
                # or submission_handle.submission_handle.over_18
            ):
                self.logger.info(f"Skip {submission_id}")
            else:
                submission_handle.load_comments(max_comm=max_num_comments)
                comments_df = submission_handle.comments2df()
                self.sql_handle.execute_values(comments_df, "reddit_comments")

    def get_date(self, created):
        return dt.datetime.fromtimestamp(created)


def parser():
    p = argparse.ArgumentParser(description="Data scraper using praw")

    p.add_argument(
        "--login_yaml", type=str, default="configs/login.yaml", help="login yaml path"
    )

    p.add_argument(
        "--subreddits",
        nargs="+",
        default=["MachineLearning"],
        type=str,
        help="List of subrredits to be scrapped",
    )

    p.add_argument(
        "--pg_host",
        type=str,
        default="localhost",
        help="Folder where h5 files are going to be saved",
    )

    p.add_argument(
        "--pg_database",
        type=str,
        default="ideaflux",
        help="Folder where h5 files are going to be saved",
    )

    p.add_argument(
        "--pg_user",
        type=str,
        default="postgres",
        help="Folder where h5 files are going to be saved",
    )

    p.add_argument(
        "--pg_password",
        type=str,
        default="postgres",
        help="Folder where h5 files are going to be saved",
    )

    p.add_argument(
        "--max_num_submissions", type=int, default=10, help="number of posts selected"
    )

    p.add_argument(
        "--max_num_comments_per_submission",
        type=int,
        default=100,
        help="number of posts selected",
    )

    return p.parse_args()


def main():
    args = parser()
    login_yaml = args.login_yaml
    subreddits = args.subreddits

    max_num_submissions = args.max_num_submissions
    max_num_comments_per_submission = args.max_num_comments_per_submission

    pg_host = args.pg_host
    pg_database = args.pg_database
    pg_user = args.pg_user
    pg_password = args.pg_password

    with open(login_yaml, "r") as file:
        yaml_file = yaml.safe_load(file)
    login = yaml_file.get("login")

    # generate reddit handler
    reddit_handle = gen_reddit(login)

    sql_handle = SQL(
        host=pg_host,
        database=pg_database,
        user=pg_user,
        password=pg_password,
    )

    data_scraper = DataScraper(
        reddit_handle=reddit_handle,
        subreddits_name_list=subreddits,
        sql_handle=sql_handle,
    )

    data_scraper.subreddit_routine(max_num_submissions=max_num_submissions)
    data_scraper.submission_routine(max_num_comments=max_num_comments_per_submission)

    sql_handle.close_conn()
    return


if __name__ == "__main__":
    main()
