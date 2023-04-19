import argparse

import yaml
from backend.analyzer import SubmissionsAnalysis
from backend.miner import DataScraper
from backend.sql import SQL
from backend.utils import gen_reddit

# python3 main.py --max_num_submissions 10 --max_num_comments_per_submission 300 --subreddits coolguides photography LifeProTips streetphotography news UnethicalLifeProTips funny confession nextfuckinglevel MachineLearning Art AskReddit DesignPorn history productivity


def parser():
    p = argparse.ArgumentParser(description="Data scraper using praw")

    p.add_argument(
        "--login_yaml", type=str, default="configs/login.yaml", help="login yaml path"
    )

    p.add_argument(
        "--subreddits",
        nargs="+",
        default=[
            "japanlife",
            "japan",
            "japanpics",
            "explainlikeimfive",
            "YouShouldKnow",
        ],
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
        "--max_num_submissions", type=int, default=3, help="number of posts selected"
    )

    p.add_argument(
        "--max_num_comments_per_submission",
        type=int,
        default=200,
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

    # # generate reddit handler
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

    sub_analysis = SubmissionsAnalysis(sql_handle=sql_handle)
    sub_analysis.routine()

    sql_handle.close_conn()
    return


if __name__ == "__main__":
    main()
