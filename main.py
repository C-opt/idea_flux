import yaml
import asyncio
import time
import threading
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.analyzer import SubmissionsAnalysis
from backend.miner import DataScraper
from backend.sql import SQL
from backend.utils import gen_reddit

# https://stackoverflow.com/questions/65916537/a-minimal-fastapi-example-loading-index-html

# frontend_app = FastAPI(title="IdeaFlux UI")
# frontend_app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


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

login_yaml = "backend/configs/login.yaml"
with open(login_yaml, "r") as file:
    yaml_file = yaml.safe_load(file)
login = yaml_file.get("login")
reddit_handle = gen_reddit(login)


app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")

templates = Jinja2Templates(directory="frontend")


# https://python.plainenglish.io/how-to-run-background-tasks-in-fastapi-python-73980fcf5672
def periodic_db_update(
    subreddit_names: list,
    max_num_submissions: int,
    max_num_comments: int,
    wait_time: int,
):
    while True:
        try:
            for subreddit_name in subreddit_names:
                data_scraper = DataScraper(
                    reddit_handle=reddit_handle,
                    subreddits_name_list=[subreddit_name],
                    sql_handle=sql_handle,
                )
                data_scraper.subreddit_routine(max_num_submissions=max_num_submissions)
                data_scraper.submission_routine(max_num_comments=max_num_comments)

                sub_analysis = SubmissionsAnalysis(sql_handle=sql_handle)
                sub_analysis.routine()
                time.sleep(wait_time)
        except Exception as e:
            print(e)
            return False


import multiprocessing


def thread_function(name):
    while True:
        print("Thread: starting", name)
        time.sleep(2)
        print("Thread: finishing", name)


@app.on_event("startup")
async def schedule_periodic_db_update():
    subreddit_names = sql_handle.get_subreddits()
    max_num_submissions = 5
    max_num_comments = 200
    wait_time = 10 * 60

    # x = threading.Thread(
    #     target=periodic_db_update,
    #     args=(subreddit_names, max_num_submissions, max_num_comments, wait_time),
    # )
    # for index in range(3):
    mining_process = multiprocessing.Process(
        target=periodic_db_update,
        args=(subreddit_names, max_num_submissions, max_num_comments, wait_time),
        daemon=True,
    )
    # threads.append(x)
    mining_process.start()
    # x.join()

    return True


@app.get("/", response_class=HTMLResponse)
async def read_item(
    request: Request,
):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.get("/subreddits")
async def get_subreddits():
    return sql_handle.get_subreddits()


@app.get("/subreddits/top{top_nth}-th")
async def get_topn_submissions(top_nth: int) -> list[dict]:
    if top_nth <= 0:
        return
    interval = "1 month"
    submissions_info = sql_handle.get_topn_submissions(top_nth, interval)
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
            "ua_rank": s_info[12],
        }
        res.append(datum)

    return res


@app.get("/subreddits/{subreddit_name}")
async def get_submissions(subreddit_name: str) -> list[dict]:
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
    max_num_submissions: int,
    max_num_comments: int,
    background_tasks: BackgroundTasks,
):
    data_scraper = DataScraper(
        reddit_handle=reddit_handle,
        subreddits_name_list=[subreddit_name],
        sql_handle=sql_handle,
    )
    background_tasks.add_task(
        data_scraper.subreddit_routine, max_num_submissions=max_num_submissions
    )
    background_tasks.add_task(
        data_scraper.submission_routine, max_num_comments=max_num_comments
    )

    sub_analysis = SubmissionsAnalysis(sql_handle=sql_handle)
    background_tasks.add_task(sub_analysis.routine)

    return True


@app.get("/submissions/{submission_id}")
async def get_comments(submission_id: str) -> list[dict]:
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
