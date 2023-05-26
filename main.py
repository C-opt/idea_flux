import multiprocessing
import time
from datetime import datetime, timedelta

import redis
import yaml
from praw import Reddit
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from app_common import SystemVariables
from rate_limiter import RateLimiter
from backend.analyzer import SubmissionsAnalysis
from backend.miner import DataScraper
from backend.redis_wrapper import RedisHashTable, RedisQueue
from backend.sql import SQL
from backend.utils import gen_reddit, timestamp

sys_vars = SystemVariables()


def sys_init():
    """
    Initiate the system variables:
        - sql_handle
        - reddit_handle
        - redis_handle
    """
    # spin up PostgreSQL handle
    host = "localhost"
    database = "ideaflux"
    user = "postgres"
    password = "postgres"
    sql_handle = SQL(
        host=host,
        database=database,
        user=user,
        password=password,
    )

    # spin up PRAW handle
    login_yaml = "backend/configs/login.yaml"
    with open(login_yaml, "r") as file:
        yaml_file = yaml.safe_load(file)
    login = yaml_file.get("login")
    reddit_handle = gen_reddit(login)

    # spin up redis wrapper(s)
    redis_url = "redis://localhost:6379"
    redis_handle = redis.from_url(redis_url)

    # instantiate rate limiter
    rate_limiter = RateLimiter(redis_handle)
    rate_limiter.add_limiter("get_/", 5, lim_max_token=1200)
    rate_limiter.add_limiter("get_/subreddits/", 5, lim_max_token=1200)
    rate_limiter.add_limiter("get_/subreddits/top-nth", 5, lim_max_token=1200)
    rate_limiter.add_limiter("get_/subreddits/subreddit_name", 5, lim_max_token=1200)
    rate_limiter.add_limiter("post_/subreddits/subreddit_name", 5, lim_max_token=1200)
    rate_limiter.add_limiter("get_/submissions/submission_id", 5, lim_max_token=1200)

    # bind it to system variables
    sys_vars["sql_handle"] = sql_handle
    sys_vars["reddit_handle"] = reddit_handle
    sys_vars["redis_handle"] = redis_handle
    sys_vars["subs_update_timestamp_table"] = RedisHashTable(
        redis_handle, "update_timestamp_table"
    )
    sys_vars["result_subreddits/top-nth"] = RedisHashTable(
        redis_handle, "subreddits/top-nth"
    )
    sys_vars["subs_update_schedule_queue"] = RedisQueue(
        redis_handle, "update_schedule_queue"
    )
    sys_vars["rate_limiter"] = rate_limiter

    return


sys_init()
app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")

templates = Jinja2Templates(directory="frontend")


def db_update(subreddit_name: str, max_num_submissions: int, max_num_comments: int):
    """Update database

    Args:
        subreddit_name (str): subreddit name to be updated
        max_num_submissions (int): max number of posts to be updated (select # hottest submissions)
        max_num_comments (int): max number of comments to be updated
    """
    reddit_handle: Reddit = sys_vars["reddit_handle"]
    sql_handle: SQL = sys_vars["sql_handle"]

    data_scraper = DataScraper(
        reddit_handle=reddit_handle,
        subreddits_name_list=[subreddit_name],
        sql_handle=sql_handle,
    )
    data_scraper.subreddit_routine(max_num_submissions=max_num_submissions)
    data_scraper.submission_routine(max_num_comments=max_num_comments)

    sub_analysis = SubmissionsAnalysis(sql_handle=sql_handle)
    sub_analysis.routine()

    return


def subreddit_scheduler(wait_time: int):
    """schedule the subreddits which are going to be updated to the DB

    Args:
        wait_time (int): wait time between the enqueues
    """
    update_timestamp_queue: RedisQueue = sys_vars["subs_update_schedule_queue"]
    sql_handle: SQL = sys_vars["sql_handle"]

    while True:
        subreddit_names = sql_handle.get_subreddits()
        try:
            for subreddit_name in subreddit_names:
                update_timestamp_queue.enqueue(subreddit_name)
                time.sleep(wait_time)
        except Exception as ex:
            raise (ex)


# https://python.plainenglish.io/how-to-run-background-tasks-in-fastapi-python-73980fcf5672
def periodic_db_update(
    max_num_submissions: int,
    max_num_comments: int,
    wait_time: int,
):
    """Periodic database update

    Args:
        subreddit_names (list): name of subreddits to look upon
        max_num_submissions (int): maximum number of posts to be looked per subreddit
        max_num_comments (int): maximum number of comments to be loaded per post
        wait_time (int): sleep waiting time between each subreddit read
    """
    update_timestamp_table: RedisHashTable = sys_vars[
        "subs_update_timestamp_table"
    ]  # hash table
    update_timestamp_queue: RedisQueue = sys_vars["subs_update_schedule_queue"]  # queue

    while True:
        try:
            # fetch a subreddit name from the queue
            subreddit_name = update_timestamp_queue.dequeue()
            update_timestamp_queue.cap_n(50)
            # print(update_timestamp_queue.length())

            # a necessary condition for updating the DB:
            # there is a subreddit name scheduled in the queue
            if subreddit_name is not None:
                subreddit_name = subreddit_name.decode()  # bytes -> string
                # for subreddit_name in subreddit_names:
                curr_ts = datetime.strptime(timestamp(), "%Y%m%d%H%M%S%f")
                last_ts = update_timestamp_table.get(subreddit_name)
                print(subreddit_name, curr_ts, last_ts)

                # if a reddit has never been updated, then
                # 1) update last_ts
                # 2) update database
                if last_ts is None:
                    db_update(subreddit_name, max_num_submissions, max_num_comments)
                    last_ts = timestamp()
                    update_timestamp_table.set(subreddit_name, last_ts)
                    time.sleep(wait_time)

                # otherwise, just read last_ts and proceed with the process
                else:
                    last_ts = last_ts.decode()  # bytes -> string
                    last_ts = datetime.strptime(last_ts, "%Y%m%d%H%M%S%f")

                    # if the latest db update on this subreddit is too early then skip
                    # that is because we don't want to spend time on an already fresh subreddit
                    if curr_ts - last_ts > timedelta(seconds=2 * 60 * 60):
                        db_update(subreddit_name, max_num_submissions, max_num_comments)
                        last_ts = timestamp()  # str
                        update_timestamp_table.set(
                            subreddit_name, last_ts
                        )  # update the last_ts
                        time.sleep(wait_time)

            # otherwise wait for a little bit
            else:
                time.sleep(wait_time)
        except Exception as ex:
            raise (ex)


@app.on_event("startup")
async def schedule_periodic_db_update():
    """Startup two processes:
    1) mining process: updates DB on a periodic fashion using a RedisHashTable & RedisQueue
    2) scheduling process: schedules which subreddits will be updated using a RedisQueue
    """
    rate_limiter: RateLimiter = sys_vars["rate_limiter"]
    max_num_submissions = 5
    max_num_comments = 200
    wait_time = 1 * 30

    mining_process = multiprocessing.Process(
        target=periodic_db_update,
        args=(max_num_submissions, max_num_comments, wait_time),
        daemon=True,
    )

    scheduling_process = multiprocessing.Process(
        target=subreddit_scheduler,
        args=(wait_time * 0.7,),
        daemon=True,
    )

    mining_process.start()
    scheduling_process.start()
    rate_limiter.init_limiters()

    return True


@app.get("/", response_class=HTMLResponse)
async def read_item(
    request: Request,
):
    """serve home page"""
    rate_limiter: RateLimiter = sys_vars["rate_limiter"]
    if not rate_limiter.have_token("get_/"):
        return False

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.get("/subreddits")
async def get_subreddits():
    """Get lists of currently read subreddits in the database

    Returns:
        list: _description_
    """
    rate_limiter: RateLimiter = sys_vars["rate_limiter"]
    if not rate_limiter.have_token("get_/subreddits/"):
        return False

    sql_handle: SQL = sys_vars["sql_handle"]
    return sql_handle.get_subreddits()


import json


@app.get("/subreddits/top{top_nth}-th")
async def get_topn_submissions(top_nth: int) -> list[dict]:
    """Get the most n-th most engaged posts within a time interval that where loaded into the DB. It uses RedisHashTable for caching the results and updating it every 15 minutes.

    Args:
        top_nth (int): the ordinal number

    Returns:
        list[dict]: the list of posts
    """
    rate_limiter: RateLimiter = sys_vars["rate_limiter"]
    if not rate_limiter.have_token("get_/subreddits/top-nth"):
        return False

    result_subreddits_top_nth_table: RedisHashTable = sys_vars[
        "result_subreddits/top-nth"
    ]
    result_subreddits_top_nth: dict = result_subreddits_top_nth_table.get(top_nth)

    if result_subreddits_top_nth is not None:
        curr_ts: datetime = datetime.strptime(timestamp(), "%Y%m%d%H%M%S%f")
        result_subreddits_top_nth: bytes = result_subreddits_top_nth.decode()
        result_subreddits_top_nth: dict = json.loads(result_subreddits_top_nth)

        last_ts = result_subreddits_top_nth.get("timestamp")
        last_ts = datetime.strptime(last_ts, "%Y%m%d%H%M%S%f")

        if curr_ts - last_ts > timedelta(seconds=15 * 60 * 60):
            res = compute_topn_submissions(top_nth)
            curr_ts = timestamp()  # str
            _tmp_str = json.dumps({"result": res, "timestamp": curr_ts})
            result_subreddits_top_nth_table.set(top_nth, _tmp_str)
            return res
        else:
            res = result_subreddits_top_nth.get("result")
            return res

    else:
        res = compute_topn_submissions(top_nth)
        curr_ts = timestamp()

        _tmp_str = json.dumps({"result": res, "timestamp": curr_ts})

        # print(result_subreddits_top_nth)
        # print(type(_tmp_dict))

        # print()
        result_subreddits_top_nth_table.set(top_nth, _tmp_str)
        return res


def compute_topn_submissions(top_nth: int, interval: str = "2 day"):
    sql_handle: SQL = sys_vars["sql_handle"]
    res = []

    if top_nth <= 0:
        return res
    submissions_info = sql_handle.get_topn_submissions(top_nth, interval)

    for s_info in submissions_info:
        datum = {
            "submission_id": s_info[0],
            "comments_num": s_info[1],
            "score": s_info[2],
            "subreddit_id": s_info[3],
            "subreddit_display_name": s_info[4],
            "title": s_info[5],
            "created": s_info[6].strftime("%Y%m%d%H%M%S%f"),
            "url": s_info[7],
            "body": s_info[8],  # body of the post; it doesn't include
            "user_engagement": s_info[10],  # user engagement score
            "spine_body": s_info[
                11
            ],  # spine body is the comment thread that has most activity within the comment section
            "ua_rank": s_info[12],  # ua_rank translates into user activity rank
        }
        res.append(datum)
    return res


@app.get("/subreddits/{subreddit_name}")
async def get_submissions(subreddit_name: str) -> list[dict]:
    """Get all submissions

    Args:
        subreddit_name (str): _description_

    Returns:
        list[dict]: _description_
    """
    rate_limiter: RateLimiter = sys_vars["rate_limiter"]
    if not rate_limiter.have_token("get_/subreddits/subreddit_name"):
        return False

    sql_handle: SQL = sys_vars["sql_handle"]
    submissions_info = sql_handle.get_submissions(subreddit_name)
    res = []

    for s_info in submissions_info:
        datum = {
            "submission_id": s_info[0],
            "comments_num": s_info[1],
            "score": s_info[2],
            "subreddit_id": s_info[3],
            "subreddit_display_name": s_info[4],
            "title": s_info[5],
            "created": s_info[6],
            "url": s_info[7],
            "body": s_info[8],
            "user_engagement": s_info[10],
            "spine_body": s_info[11],
        }
        res.append(datum)
    return res


@app.post("/subreddits/{subreddit_name}")
async def update_submissions(
    subreddit_name: str,
):
    """_summary_

    Args:
        subreddit_name (str): _description_

    Returns:
        _type_: _description_
    """
    rate_limiter: RateLimiter = sys_vars["rate_limiter"]
    if not rate_limiter.have_token("post_/subreddits/subreddit_name"):
        return False

    update_timestamp_queue: RedisQueue = sys_vars["subs_update_schedule_queue"]
    try:
        update_timestamp_queue.enqueue(subreddit_name)
    except Exception as ex:
        raise (ex)
    return True


@app.get("/submissions/{submission_id}")
async def get_comments(submission_id: str) -> list[dict]:
    """Get all comments of a submission (post)

    Args:
        submission_id (str): submission id

    Returns:
        list[dict]: list of comments of the submission (aka post)
    """
    rate_limiter: RateLimiter = sys_vars["rate_limiter"]
    if not rate_limiter.have_token("get_/submissions/submission_id"):
        return False

    sql_handle: SQL = sys_vars["sql_handle"]
    comments_info = sql_handle.get_comments(submission_id)

    res = []
    for c_info in comments_info:
        datum = {
            "comment_id": c_info[0],
            "parent_id": c_info[1],
            "submission_id": c_info[2],
            "body": c_info[3],
        }
        res.append(datum)
    return res
