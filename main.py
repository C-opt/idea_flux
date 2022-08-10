import os
import pandas as pd
import yaml
import argparse
from utils import gen_reddit
from __class_data_scrapper import DataScraper
from __class_graph_analysis import GraphsAnalysis

def parser():
    parser = argparse.ArgumentParser("IdeaFlux main function.")

    parser.add_argument("--h5_dir", type=str, default="data/20220810/", help="h5 dir")

    parser.add_argument("--res_dir", type=str, default="data/20220810/", help="results dir")
    
    parser.add_argument("--topics_df_fp", type=str, default="data/20220810/topics_df.h5", help="filepath to master h5 (dataframe when accessed)")

    parser.add_argument("--login_yaml_fp", type=str, default="login.yaml",
                        help="login yaml path")

    parser.add_argument("--subreddits", nargs="+", default=["japanlife", "japan"], type=str, help="List of subrredits to be scrapped")
    
    parser.add_argument("--save_dir", type=str, default="data/20220810/",
                        help="folder where h5 files are going to be saved")

    parser.add_argument("--top_num_posts", type=int, default=5,
                        help="number of posts selected")

    return parser.parse_args()

def main():

    args = parser()

    login_yaml_fp = args.login_yaml_fp
    save_dir = args.save_dir
    top_num_posts = args.top_num_posts
    subreddits_list = args.subreddits
    h5_dir = args.h5_dir
    res_dir = args.res_dir
    topics_df_fp = args.topics_df_fp

    with open(login_yaml_fp, "r") as file: 
        yaml_file = yaml.safe_load(file)
    login = yaml_file.get("login")
    
    # # generate reddit handler
    reddit = gen_reddit(login)

    data_scraper = DataScraper(save_dir=save_dir, reddit_handle=reddit, subreddits_list=subreddits_list)
    data_scraper.dl_df_routine(top_num=top_num_posts)
    graphs_analysis = GraphsAnalysis(h5_dir=h5_dir, res_dir=res_dir, topics_df_fp=topics_df_fp)
    graphs_analysis.batch_summarization()

if __name__ == "__main__":
    main()
