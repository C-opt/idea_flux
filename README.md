# idea_flux
IdeaFlux is a Reddit comments summarization tool using praw & Networkx. 
## Description
IdeaFlux scrapes and summarizes comments of top subrredits of your choice by selecting which comment generated most comments: 
- The root node is the topic itself and it greedly selects the most "prosperous" comment, then outputs it in a text file;
- Then this parent comment will select the most prosperous child node, then outputs it in a text file once again;
- Then this process repeats recursively until reaching the leaf node.

Also IdeaFlux generates the graphic visualization of the comment network, giving an overall idea of how the conversation of a particular topic is being branched out.

Additionally, IdeaFlux gives a conversation engagement score for each topic posted and niftly list it up in an Excel file. 
## Dependencies
- networkx
- praw
- requests
## Usage
- First of all, you need a reddit account
- Then you are going to need 
- For scraping reddit data
```
python3 __class_data_scrapper.py --login_yaml_fp login.yaml --subrredit MachineLearning --save_dir data/ --top_num_posts 10
```

- For analyzing scrapped data
```
python3 __class_graph_analysis.py --h5_dir data/ --res_dir data/ --topics_df_fp data/topics_df.h5
```
- For scraping then analyzing it, then simply
```
python3 main.py 
```
