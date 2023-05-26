# What is IdeaFlux?
Ideaflux is a Reddit comment mining tool. It uses comments structure for heuristically selecting a single thread of comments that appears to be the most interesting in terms of comment engagement. 
# Core capabilities
IdeaFlux is able to 
- mine comments of any Reddit subreddit into a database
- rank comment sections of posts in terms of user engagement 
- output the interesting submissions through an API
- generate data visualization of the interesting submissions through a webpage 
# Usage examples
## RSS feed
This can be used as-is. All you need to do is access [this website]. Here is a snapshot of it: 
## SEO
## Mine comments for fine tuning ChatGPT models


# Requirements for spinning up your own IdeaFlux
## Get reddit API key
- First of all, you need a Reddit account
- Then you are going to need to create an app within reddit to get the OAuth2 keys to access the API. For more info on that matter, see the section "The Reddit API" on https://www.storybench.org/how-to-scrape-reddit-with-python/. Generating the keys is easier than you might think.
- After that, you need to generate a yaml file (login.yaml) with your credentials for the application then place it in project's root directory. You can easily do that using tools such as https://codebeautify.org/yaml-editor-online. The file must follow the template below:
```yaml
login: 
    client_id: [API client ID]
    client_secret: [API client secret]
    user_agent: [API name]
    username: [your reddit username]
    password: [your reddit password]
```
- then place login.yaml in path/to/backend/configs/
## Install dependencies in venv
```bash
pip install -r requirements.txt
```
## Prepare postgreSQL server

```bash
sudo service postgresql start
```
## Startup Redis server
```bash
redis-server
```
## Startup FastAPI
```bash
uvicorn main:app --reload
```


# Technical details
## Intro
The core of Ideaflux is the following. IdeaFlux summarizes comments of top posts of subreddits of your choice by recursively selecting which comment generated most comments: 
- The root node is the topic itself and it greedly selects the most prosperous comment, the one that generated most comments, then outputs it in a text file;
- Then this parent comment will select the most prosperous child node;
- Then this process is repeated recursively until it reaches the leaf node.
## Code structure
For backend, IdeaFlux stores all the mined data in postreSQL, a simple task queue system and caching system is implemented using Redis, and the APIs are served using FastAPI. For frontend, we use d3.js for data visualization of the most interesting posts in Reddit.
### Backend
There are two database systems: postgreSQL, and Redis. 

PostgreSQL has three main tables (submissions, reddit_comments, submissions_user_engagement), that can be created using the following queries:
```SQL
CREATE TABLE submissions (
  submission_id CHAR PRIMARY KEY,
  comments_num FLOAT,
  subreddit_id VARCHAR,
  subreddit_display_name VARCHAR,
  title VARCHAR,
  created TIMESTAMP,
  url VARCHAR,
  body VARCHAR
);
```
```SQL
CREATE TABLE reddit_comments (
  comment_id CHAR PRIMARY KEY,
  parent_id VARCHAR,
  submission_id VARCHAR,
  body VARCHAR
);
```
```SQL
CREATE TABLE submissions_user_engagement (
  submission_id CHAR PRIMARY KEY,
  user_engagement FLOAT NOT NULL,
  spine_body VARCHAR
);
```



Redis has two objects (hash table, task queue). 

FastAPI has the following APIs.    
### Frontend

# Commonly used SQL queries
- Check what tables exist in DB
```SQL
SELECT * FROM information_schema.tables WHERE table_schema = 'public'
```

- Get list of subreddits names that have been mined
```SQL
SELECT DISTINCT subreddit_display_name FROM submissions
```

- Get list of comments for a given submission id
```SQL
SELECT * FROM reddit_comments 
WHERE submission_id = '{submission_id}';
```

- Get list of submissions (posts) for an arbitrary subreddit having the user engagement score sorted in descendent order
```SQL
  SELECT *
  FROM
      submissions
  INNER JOIN 
      submissions_user_engagement
  ON 
      submissions_user_engagement.submission_id = submissions.submission_id
  WHERE
      submissions.subreddit_display_name = '{subreddit_name}'
  ORDER BY
      user_engagement DESC;
```

- Get list of submissions (posts) that are top 5 for each subreddit within one day, and sorted by decreasing user engagement score
```SQL
  SELECT *
  FROM (
      SELECT 
          *, ROW_NUMBER() OVER (PARTITION BY submissions.subreddit_id ORDER BY user_engagement DESC) AS ua_rank
      FROM
          submissions
      INNER JOIN 
          submissions_user_engagement
      ON 
          submissions_user_engagement.submission_id = submissions.submission_id
      WHERE created > now() - interval '1 days'
      ORDER BY
      user_engagement DESC
  ) ranks
  WHERE ua_rank <= 5
```
# ToDo
- [x] program SQL table init for new env
- [x] improve logging messages
- [x] write commonly used SQL queries
- [x] implement rate-limiter to APIs
- [x] improve javascript responsiveness (PC/tablet/phone)
- [x] implement memory cache for /subreddits/top{top_nth}-th using Redis
- [ ] implement redirect page (in case of too many requests)
- [ ] make tooltip more evident (frontend)
- [ ] add unit tests to FastAPI
- [ ] deploy API to AWS
 


