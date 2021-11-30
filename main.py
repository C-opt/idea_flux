import os
import pandas as pd
import yaml
from utils import gen_reddit
from __class_data_scraper import DataScraper
from __class_graph_analysis import GraphAnalysis
from __class_graph_analysis import GraphsAnalysis

def main():

    with open("login.yaml", "r") as file: 
        yaml_file = yaml.safe_load(file)
    login = yaml_file.get("login")
    
    # # generate reddit handler
    reddit = gen_reddit(login)

    subreddits_list = list()
    subreddits_list.append("MachineLearning")
    subreddits_list.append("askscience")
    # subreddits_list.append("productivity")
    # subreddits_list.append("CasualConversation")
    # subreddits_list.append("Stoicism")
    # subreddits_list.append("optimisemylife")
    # subreddits_list.append("EverythingScience")
    
    # for subreddit in reddit.subreddits.default(limit=None):
    #     top_subrredits.append(str(subreddit))
    #     print(str(subreddit))
    data_scraper = DataScraper(save_dir="data/", reddit_handle=reddit, subreddits_list=subreddits_list)
    data_scraper.dl_df_routine(top_num=5)

    h5_dir = "data/"
    res_dir = "data/"
    topics_df_fp = "data/topics_df.h5"

    graphs_analysis = GraphsAnalysis(h5_dir=h5_dir, res_dir=res_dir, topics_df_fp=topics_df_fp)
    graphs_analysis.batch_summarization()

if __name__ == "__main__":
    main()
