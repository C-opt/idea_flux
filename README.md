# idea_flux
IdeaFlux is a Reddit comments summarization tool using praw & Networkx. 
## Description
IdeaFlux summarizes comments of top subrredits of your choice by selecting which comment generated most comments: 
- The graph root node is the topic itself and it greedly selects the most "prosperous" comment, then outputs it in a text file;
- Then this parent comment will select the most prosperous child node;
- Then this process repeats recursively until reaching leaf nodes.
## Dependencies
- networkx
- praw
- requests
## Usage
- For scraping reddit data
python3 __class_data_scrapper.py --login_yaml_fp login.yaml --subrredit MachineLearning --save_dir data/ --top_num_posts 10
- For analyzing scrapped data
python3 __class_graph_analysis.py --h5_dir data/ --res_dir data/ --topics_df_fp data/topics_df.h5
- For scraping then analyzing it, then simply
python3 main.py 
