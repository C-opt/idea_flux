# IdeaFlux
IdeaFlux is a Reddit comments text mining tool that uses praw & Networkx. It uses the Reddit's comments structure for heuristically selecting a single thread that appears to be the most interesting in terms of comment engagement.

## Description
In a nutshell, IdeaFlux summarizes comments of top posts of subreddits of your choice by recursively selecting which comment generated most comments: 
- The root node is the topic itself and it greedly selects the most "prosperous" comment, then outputs it in a text file;
- Then this parent comment will select the most prosperous child node, then outputs it in a text file once again;
- Then this process is repeated recursively until it reaches the leaf node.

The outputted text file should look like something like this

```
Title:Recruiters of Reddit, why are you always looking for a unicorn candidate?
URL: https://www.reddit.com/r/recruitinghell/comments/s02lqa/recruiters_of_reddit_why_are_you_always_looking/
This is going to be the same on the side of a job candidate. You can find a job that you love but there's still going to be some things that you don't like about it nothing is 100% perfect. Perfection is an unrealistic expectation and I don't understand why employers X out pretty much everyone, And not to mention all the stress and pressure They put a job candidate under in the interview. I feel there is the worst candidate, A good candidate, And the best candidate but there is no unicorn candidate that can do everything and have everything that you want. As everyone else is saying employers are offering very low wages for jobs They need to fill. I'm talking about skilled positions. I for in, for instance,stance have specific experience in the construction industry and I've been applying to jobs the postings I've seen list all the credentials that I have but the pay is so low it's Ridiculous. I feel like pay should be dependent on experience and there should be an open negotiation there shouldn't be just a flat rate salary or Hourly wage on the posting.
----------TITLE----------
Topic engagement score: 7.489690721649485
----------------------------------------
Comment ID: hrz1v5s
Comment score: 66
Comment body: The desire to have “unicorn” candidates comes from the hiring manager, not the recruiter.  Recruiters are simply seeking out the type of candidate a hiring manager has asked for.
----------------------------------------
Comment ID: hrzv4wu
Comment score: 35
Comment body: When a recruiter doesn't temper expectations they are just a Con Artist taking advantage of a mark then.

I can have a dozen people demanding I sell them the Maltese Falcon but if I don't have it, i am a grifter no matter their level of demand.
----------------------------------------
Comment ID: hs03h82
Comment score: 33
Comment body: Yeah, managing expectations is a huge part of being a recruiter.  Recruiters bring market data to the hiring managers and try and find the candidate that aligns closest to the requirements if they are “unicorn” requirements that can’t truly be filled, but ultimately the hiring manager gets final say. Recruiters act as the liaison between the business and the candidates and as a result they are often the messenger of bad news that is coming from somewhere way above their pay grade.
----------------------------------------
Comment ID: hs2h9us
Comment score: 32
Comment body: "market data" = things that they noticed after making a couple of calls or just surfing the internet real quick.
----------------------------------------
[text continues]
```

Also IdeaFlux generates a graphic visualization of the comment network, giving an overall idea of how the conversation of a particular topic is being branched out. For example, a visualization of the comment network of the post above is as follows.

<img src="https://github.com/C-opt/idea_flux/blob/master/github_data/s02lqa.png?raw=true" width=90% height=75%>

Additionally, IdeaFlux gives a user engagement score for each topic posted and lists it up in an XLSX file. How this score is calculated, and its mathematical analysis are discussed in the User Engagement Score section. 

<img src="https://github.com/C-opt/idea_flux/blob/master/github_data/topics_df.png?raw=true" width=100% height=100%>

## Main dependencies
- python 3.7
- networkx 
- praw
- requests

## Usage
- First of all, you need a Reddit account
- Then you are going to need to create an app within reddit to get the OAuth2 keys to access the API. For more info on that matter, see the section "The Reddit API" on https://www.storybench.org/how-to-scrape-reddit-with-python/. Generating the keys is easier than you might think.
- After that, you need to generate a yaml file (login.yaml) with your credentials for the application then place it in project's root directory. You can easily do that using tools such as https://codebeautify.org/yaml-editor-online. The file must follow the template below:
```
login: 
    client_id: API client ID
    client_secret: API client secret
    user_agent: API name
    username: your reddit username
    password: your reddit password
```
- Then you scrap comments from currently 10 "hottest" topics from your favorite subrredit and save it as {topic_id}.h5 file in data/ 
```
python3 __class_data_scrapper.py --login_yaml_fp login.yaml --subrredits MachineLearning cscareerquestions --save_dir data/ --top_num_posts 10
```

- And finally, you read the .h5 files and output the results in res_dir
```
python3 __class_graph_analysis.py --h5_dir data/ --res_dir data/ --topics_df_fp data/topics_df.h5
```
The outputs are 
1. comments summary text files for each h5 file
2. the graph corresponding to each h5
3. topics_df.xlsx, which contains the summary of all topics in h5_dir
- For automatically doing both things, that is, data scraping and analyzing it, then simply execute
```
python3 main.py --h5_dir data/ --res_dir data/ --topics_df_fp data/topics_df.h5 --login_yaml_fp login.yaml --subrredits MachineLearning cscareerquestions --save_dir data/ --top_num_posts 10
```
## User engagement score
### Description 
IdeaFlux gauges how a given topic is generating conversation by calculating "user engagement score". The higher this number is, the more engaged the comments section is. 

The calculation of it is simple: the average of the number of descendants of all nodes. 

That should give a number between 0 and n, where n is the number of comments of a given topic. Why do it like that? Read on the next section.
### Motivation & Analysis
Given a fixed number of comments, how can we measure the conversation engagement of a given topic? That is, given a fixed n, how can we measure the branching factor of different comments graphs?

Let's illustrate the current measurement with two possible comments sections:
- Sun-like graph
- Queue graph

## Common issues
- Comments scrapping might take some time depending on which subreddit you want to scrap. The data scraper takes more time to process comments of subreddits that are largely popular due to the sheer amount of it. Even more because praw forcifully sleeps the comment retriever every 20 comments or so after the 200 comments mark (not sure about the numbers here; please let me know if any of you have more experience with praw). 
- Opening the comments graph's  html file might take some time for more than 500 of comments.

## Resources
- https://pythonprogramming.net/parsing-comments-python-reddit-api-wrapper-praw-tutorial/
- https://towardsdatascience.com/visualizing-networks-in-python-d70f4cbeb259
- https://www.storybench.org/how-to-scrape-reddit-with-python/
