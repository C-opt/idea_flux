from pandas.core.frame import DataFrame
import logging
import requests
import datetime as dt
import pandas as pd
import io
import cv2
import numpy as np
from PIL import Image
import logging
import time
import os
import yaml
import argparse

from utils import create_directory
from utils import gen_reddit


class DataScraper():
    def __init__(self, **kwargs):
        self.setup_logging()
        self.subreddits_list = kwargs.get("subreddits_list")
        self.reddit_handle = kwargs.get("reddit_handle")
        self.save_dir = kwargs.get("save_dir")
        return

    def setup_logging(self, log_level=logging.DEBUG):

        # 
        FORMAT = "%(asctime)s %(levelname)7s %(filename)20s:%(lineno)4s - %(name)15s.%(funcName)16s() %(message)s"

        log_dir = "logs/"
        log_file = log_dir + "{name}.log".format(name=type(self).__name__)
        create_directory(log_dir)
        if not os.path.exists(log_file):
            with open(log_file, "w+") as f:
                f.write("-------------- LOG FILE FOR {name} --------------\n".format(name=type(self).__name__))

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

    def topics_dict_init(self):
        topics_dict = dict()
        topics_dict.update({"title":list()})
        topics_dict.update({"score":list()})
        topics_dict.update({"id":list()})
        topics_dict.update({"url":list()})
        topics_dict.update({"comms_num":list()})
        topics_dict.update({"created":list()})
        topics_dict.update({"body":list()})
        topics_dict.update({"user_engagement":list()})

        return topics_dict

    def topics_dict2df(self, subreddit, limit=100):
        
        topics_dict = self.topics_dict_init()
        for submission in subreddit.hot(limit=limit):
            
            topics_dict.get("title").append(submission.title)
            topics_dict.get("score").append(submission.score)
            topics_dict.get("id").append(submission.id)
            topics_dict.get("url").append(submission.url)
            topics_dict.get("comms_num").append(submission.num_comments)
            topics_dict.get("created").append(submission.created)
            topics_dict.get("body").append(submission.selftext)
            topics_dict.get("user_engagement").append(-1)

            # assume you have a Reddit instance bound to variable `reddit`
            # top_level_comments = list(submission.comments)
            #submission.comment_sort = "top"
            #topics_dict.get("comments").append(list(submission.comments))

        topics_data = pd.DataFrame(topics_dict)
        return topics_data


    def data_scraper(self, subreddit_name="itookapicture", limit=100):
        
        subreddit = self.reddit_handle.subreddit(subreddit_name)
        topics_data = self.topics_dict2df(subreddit, limit=limit)
        return topics_data

    def get_date(self, created):
        return dt.datetime.fromtimestamp(created)

    def receive_image(self, url, filepath):
        self.logger.info("downloading {fp} from {url}".format(fp=filepath, url=url))
        try:
            response = requests.get(url, timeout=10.0)
        except Exception as err:
            self.logger.error("Response error occurred: {err}".format(err=err))
            return None

        if response.status_code == 200:
            try:
                file = io.BytesIO(response.content)
                img = Image.open(file)
                img = np.array(img)
                img = img[:, :, ::-1]
                img = img.copy(order="C")
                
                cv2.imwrite(filepath, img)
                return img
            except Exception as err:
                self.logger.error("Image error: {err}".format(err=err))
                return None

    def dl_images(self, images_subreddits, limit=20):
        for image_subreddit_name in self.subreddits_list:
            
            df = self.data_scraper(subreddit_name=image_subreddit_name, limit=100)

            #correct timestamp
            _timestamp = df.get("created").apply(self.get_date)
            df = df.assign(timestamp = _timestamp)
            sorted_df = df.sort_values(by="comms_num", ascending=False)

            urls = sorted_df.get("url").values
            for url in urls[:limit]:

                str_split = url.split("/")
                filename = str_split[len(str_split) - 1]
                self.receive_image(url, "images/" + filename)

        return


    def parse_comms(self, subid, max_comm=200):
        #comment.parent() = praw.models.reddit.comment.Comment
        submission = self.reddit_handle.submission(subid)
        # if submission.stickied: return None

        self.logger.info("comments.replace_more()  ...")
        t0 = time.time()
        while True: 
            try: 
                submission.comments.replace_more(limit=max_comm)
                break
            except PossibleExceptions as e:
                self.logger.error("handing comments.replace_more(limit=max_comm): {e}".format(e=e))
                time.sleep(1.0)
        t1 = time.time()
        self.logger.info("comments.replace_more() in {comms_replace_time:4.2f} seconds".format(comms_replace_time=t1-t0))
        
        
        comm_dict = dict()
        comm_dict.update({"parent_id":list()})
        comm_dict.update({"comm_id":list()})
        comm_dict.update({"body":list()})
        comm_dict.update({"weight":list()})
        comm_dict.update({"type":list()})

        self.logger.info("comments.list() ...")
        t0 = time.time()
        comms_list = submission.comments.list()
        t1 = time.time()
        self.logger.info("comments.list() in {comms_list_time:4.2f} seconds".format(comms_list_time=t1-t0))

        self.logger.info("parsing comments of " + subid)
        for comment in comms_list[:max_comm]:
    #         print(20*"#")
    #         print("Parent ID: ", comment.parent())
    #         print("Comment ID: ", comment.id)
    #         print(comment.body)
            
            comm_dict.get("parent_id").append(comment.parent().id)
            comm_dict.get("comm_id").append(comment.id)
            comm_dict.get("body").append(comment.body)
            comm_dict.get("type").append("Undirected")
            comm_dict.get("weight").append(1)

        comm_df = pd.DataFrame(comm_dict)
        return comm_df

    def save_df(self, filepath, df):
        self.logger.info("saving dataframe to ... {filepath}".format(filepath=filepath))
        return df.to_hdf(filepath, key="df")

    def dl_df_routine(self, top_num=5):
        topics_df = pd.DataFrame()
        # save_dir = "data/"
        create_directory(self.save_dir)
        self.logger.info("-"*50)
        self.logger.info("initating dl_df_routine")

        for subrredit_name in self.subreddits_list:
            self.logger.info("-"*50)
            self.logger.info("parsing top {top_num}-th in {subrredit_name}".format(top_num=top_num, subrredit_name=subrredit_name))
            
            # dashboard of a single subreddit (subreddit_name)
            df = self.data_scraper(subreddit_name=subrredit_name, limit=100)
            _timestamp = df.get("created").apply(self.get_date)
            df = df.assign(timestamp = _timestamp)
            df = df.sort_values(by="comms_num", ascending=False)
            topics_df = topics_df.append(df[:top_num])
            
            most_comm_posts = list(df["id"])[:top_num]
            for post_id in most_comm_posts:
                self.logger.info("parsing top {top_num}-th in {subrredit_name}: {post_id}".format(top_num=top_num,subrredit_name=subrredit_name, post_id=post_id))
                # parse comments given a post_id (probably filtered thru the above df)
                comm_df = self.parse_comms(post_id, max_comm=20000)
                save_filepath = self.save_dir+post_id+".h5"
                self.save_df(save_filepath, comm_df)

        topics_df = topics_df.reset_index(drop=True)
        self.save_df(self.save_dir+"topics_df.h5", topics_df)
        return 

def parser():
    parser = argparse.ArgumentParser(description="Data scraper using praw")

    parser.add_argument("--login_yaml_fp", type=str, default="login.yaml",
                        help="login yaml path")

    parser.add_argument("--subreddits", nargs="+", default=["MachineLearning"], type=str, help="subrredits to be scrapped")
    
    parser.add_argument("--save_dir", type=str, default="data/",
                        help="folder where h5 files are going to be saved")

    parser.add_argument("--top_num_posts", type=int, default=5,
                        help="number of posts selected")
    
    return parser.parse_args()

def main():
    args = parser()
    login_yaml_fp = args.login_yaml_fp
    subreddits = args.subreddits
    save_dir = args.save_dir
    top_num_posts = args.top_num_posts

    with open(login_yaml_fp, "r") as file: 
        yaml_file = yaml.safe_load(file)
    login = yaml_file.get("login")
    
    # # generate reddit handler
    reddit = gen_reddit(login)

    # subreddits_list = list()
    # subreddits_list.append(subreddit)

    data_scraper = DataScraper(save_dir=save_dir, reddit_handle=reddit, subreddits_list=subreddits)
    data_scraper.dl_df_routine(top_num=top_num_posts)
    return

if __name__=="__main__":
    main()
