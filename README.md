# idea_flux
IdeaFlux is a Reddit comments summarization tool using praw & Networkx. 
## Description
IdeaFlux summarizes comments of top subrredits of your choice by selecting which comment generated most comments: 
- The graph root node is the topic itself and it greedly selects the most "prosperous" comment, then outputs it in a text file;
- Then this parent comment will select the most prosperous child node;
- Then this process repeats recursively until reaching leaf nodes.
