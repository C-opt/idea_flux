# idea_flux
IdeaFlux is a Reddit comments summarization tool using praw & Networkx. It uses the comments structure of Reddit (comments of comments of comments of [...]) for greedily selecting a single thread that seems to be the most interesting in terms of conversation engagement. 
## Description
In a nutshell, it summarizes comments of top subrredits of your choice by selecting which comment generated most comments: 
- The root node is the topic itself and it greedly selects the most "prosperous" comment, then outputs it in a text file;
- Then this parent comment will select the most prosperous child node, then outputs it in a text file once again;
- Then this process is repeated recursively until it reaches the leaf node.

The outputted text file should look like something like this

```
Title:[D] What are your long term career goals ? 10+ years
URL: https://www.reddit.com/r/MachineLearning/comments/r18rjz/d_what_are_your_long_term_career_goals_10_years/
Hello guys, I am trying to figure out long term goals for myself as I feel that I reached some plateau as senior ML engineer. I was wondering what other people in the field long term career goals were ?
----------TITLE----------
Topic engagement score: 2.8553459119496853
----------------------------------------
Comment ID: hlxhm2b
Comment score: 28
Comment body: I came to the US with a future plan of working in cutting-edge ML, but I recently learned how good the money is in simple SWE jobs... I'm honestly torn.
----------------------------------------
Comment ID: hlxjg64
Comment score: 25
Comment body: What defines a "Simple" SWE job to you?
----------------------------------------
Comment ID: hlxxzmh
Comment score: 24
Comment body: And surely ML jobs pays better than SWE jobs, no?
----------------------------------------
Comment ID: hly6kfo
Comment score: 14
Comment body: ML hasn’t exploded yet, it’s still in infancy. 5 years ago the jobs of data engineer, ml engineer, and data scientists were under the data scientist title. Some companies still do this, but it’s slowly changing. More and more companies will need ML engineers the same way more and more companies started needing developer.
----------------------------------------
Comment ID: hlyael9
Comment score: 10
Comment body: I expect the opposite.

As ML matures, it'll be just another standard software tool (like linear regression, or sorting algorithms, or video compression libraries) that every SWE will be expected to be able to use.

I think the video compression analogy is a good one.  Back in the late 1990's many companies (Sony, RealNetworks, C-Cube, etc)  had video compression PhDs tweaking algorithms in the same way we tweak DL models today.  Like ML, video compression involved heavy math and similar tradeoffs of computation-vs-accuracy.    Today, 99.9% of software engineers dealing with video neither know nor care about the math behind H.265.  Sure there a still a couple companies that hire a couple PhDs working on successors to H.266/MPEG-5; and a couple university guys playing with wavelet transforms.

in a couple decades I'm guessing 99% of ML work will just be calling `fit_non_liner_curve(my_data)`, and the libraries themselves will pick a reasonable architecture/model/hyperparameters/etc for the data; in much the same way we call `compress_my_video(frames)` today and it picks reasonable algorithms and default parameters for us.   Sure there'll still be PhDs working with Nvidia on future tweaks to tensor cores; and university PhDs writing papers on slightly differently curved activation functions.   But I think there'll be even fewer of those jobs than there are today.
...
[text file continues]
...
```

Also IdeaFlux generates the graphic visualization of the comment network, giving an overall idea of how the conversation of a particular topic is being branched out.

<img src="https://github.com/C-opt/idea_flux/blob/master/data/r18rjz.png?raw=true" width=50% height=50%>

Additionally, IdeaFlux gives a conversation engagement score for each topic posted and niftly list it up in an Excel file. 

## Dependencies
- networkx
- praw
- requests
## Usage
- First of all, you need a reddit account
- Then you are going to need to create an app within reddit to get the OAuth2 keys to access the API. For more info on that matter, see https://www.storybench.org/how-to-scrape-reddit-with-python/. It is easier than you might think.
- After that, you need to generate a yaml file (login.yaml) with your credentials for the application. You can easily do that using tools such as https://codebeautify.org/yaml-editor-online. 
```
login: 
    client_id: API client ID
    client_secret: API client secret
    user_agent: API name
    username: your reddit username
    password: your reddit password
```
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
## Topic engagement score
### Description 
IdeaFlux gauges how a given topic is generating conversation by calculating "topic engagement score". The higher this number is, the more engaged the comments section. 

The calculation of it is fairly simple: it is the average of the number of descendants of all nodes. 

That should give a number between 0 and n, where n is the number of comments of a given topic.
## Resources
- https://pythonprogramming.net/parsing-comments-python-reddit-api-wrapper-praw-tutorial/
- https://towardsdatascience.com/visualizing-networks-in-python-d70f4cbeb259
- https://www.storybench.org/how-to-scrape-reddit-with-python/
