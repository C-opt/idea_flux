# IdeaFlux
IdeaFlux is a Reddit comments text mining tool that uses praw & Networkx. It uses the Reddit's comments structure for heuristically selecting a single thread that appears to be the most interesting in terms of comment engagement.

## Description
In a nutshell, IdeaFlux summarizes comments of top posts of subreddits of your choice by recursively selecting which comment generated most comments: 
- The root node is the topic itself and it greedly selects the most "prosperous" comment, then outputs it in a text file;
- Then this parent comment will select the most prosperous child node, then outputs it in a text file once again;
- Then this process is repeated recursively until it reaches the leaf node.

The outputted text file should look like something like this

```
Title:After 4 interviews, rejected for eating a cornflake.
URL: https://www.reddit.com/r/recruitinghell/comments/rzq9dc/after_4_interviews_rejected_for_eating_a_cornflake/
I've had 4 interviews at this place. At the last one, with some of the seniors, I've arrived on time. I've waited in the kitchen, and they just casually chatted while making a toast. 

You can sense they're two goofballs. After a while, I joined them since it was just weird and they offered me to get something to eat. I wasn't really familiar with the kitchen but I saw a cornflakes dispenser and I put some in a disposable cup.

They then said, great let's go to the interview. We do it very casually, we laugh a lot, and say our goodbyes.

I now recieved a phone call that I didn't get in because I took 3-4 cornflakes while we were there. It's a hightech job. I knew all the technical questions and was told by the HR that that's what they said.

What do you think? Was this justified? I get that it would seem like an unusual situation but it was their idea to get it and it felt a lot like a casual get-to-know-you chat.

Thanks ahead!

UPDATE and EDIT:

* the interview was not in the kitchen, I waited in the kitchen while the manager made himself a toast which he ate in the kitchen. This is well after we should’ve met. The interview was in a meeting room. 
* they sort of insisted I take something from the kitchen and the cornflakes were closest, so I took it.
* I’m not supposed to know that it’s the cornflakes, I was told that in confidence by the middleman HR company 
* curious, I just called them to see what they have to say, since everything went so well. She told me “I’ll talk to everyone who interviewed you along the way and get back to you”
* I ask for less than the market usually pays for this job since I’m not as experienced. I asked them to talk over if it’s a money issue to which she said that shouldn’t be a problem, and if it would be, we could discuss something that works.
----------TITLE----------
Topic engagement score: 3.3808695652173912
----------------------------------------
Comment ID: hrwmqch
Comment score: 146
Comment body: Yup. Crappy HR trap. I’m not HR but in my last position I used to do some interviews. I was once forced to reject a candidate because when I offered something to drink she asked for a Coke…

Apparently, according to the HR nut job, if you ask for a Coke you don’t care about yourself therefore you won’t care about your job.

Also, I remember a candidate being invited to join us to the company lunch before Christmas. Rejected for overconfidence.
----------------------------------------
Comment ID: hrwofkz
Comment score: 27
Comment body: OOC, what would be the "correct" answer in that case? Coffee? Water? Nothing thank you? Do-you-have-any-good-loose-leaf-teas?
----------------------------------------
[text continues]
```

Also IdeaFlux generates a graphic visualization of the comment network, giving an overall idea of how the conversation of a particular topic is being branched out.

<img src="https://github.com/C-opt/idea_flux/blob/master/github_data/rzq9dc.png?raw=true" width=90% height=75%>

Additionally, IdeaFlux gives a user engagement score for each topic posted and niftly list it up in an Excel file. How this score is calculated, and its mathematical analysis is further discussed in the section "user engagement score". 

<img src="https://github.com/C-opt/idea_flux/blob/master/data/topics_df.jpg?raw=true" width=100% height=100%>

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
python3 __class_data_scrapper.py --login_yaml_fp login.yaml --subrredit MachineLearning --save_dir data/ --top_num_posts 10
```

- And finally, you read the .h5 files and output the results in res_dir
```
python3 __class_graph_analysis.py --h5_dir data/ --res_dir data/ --topics_df_fp data/topics_df.h5
```
The outputs are 
1. comments summary text files for each h5 file
2. the graph corresponding to each h5
3. topics_df.xlsx, which contains the summary of all topics in h5_dir
- For automatically data scraping and analyzing it, then simply execute
```
python3 main.py 
```
## User engagement score
### Description 
IdeaFlux gauges how a given topic is generating conversation by calculating "user engagement score". The higher this number is, the more engaged the comments section is. 

The calculation of it is simple: the average of the number of descendants of all nodes. 

That should give a number between 0 and n, where n is the number of comments of a given topic. Why do it like that? Read on the next section.
### Motivation & Analysis
Given a fixed number of comments, how can we measure the conversation engagement of a given topic? That is, given a fixed n, how can we measure the branching factor of different comments graphs?

Let's illustrate it with two examples with n = 5
- Sun-like graph
- Queue graph

## Common issues
- Comments scrapping might take some time depending on which subreddit you want to scrap (MachineLearning = fast; askreddit = very slow);
- Opening the comments graph (the html file) might take some time for >500 of comments.

## Resources
- https://pythonprogramming.net/parsing-comments-python-reddit-api-wrapper-praw-tutorial/
- https://towardsdatascience.com/visualizing-networks-in-python-d70f4cbeb259
- https://www.storybench.org/how-to-scrape-reddit-with-python/
