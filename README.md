NBA_Predictions_V4
==================

Reworked NBA Predictions (Python Version)

I've decided to rework my NBA Prediction code from R to Python.  Mostly to see if I could do it, and also to see if I could speed it up a bit.  I'll update here with current speed/accuracy results as the 2014-15 season plays out. The structure and format is pretty much the same, with the exception that it's cleaner code.  I still need to comment it a bit more, but it's Git ready for now.

Overview of Files:
==================

1) NBA_Driver.py - This is the workhorse, the script that actually gets run.  It will call the webscrapers, genetic functions, and create the data/logging as it runs.

2) NBA_Tweeter.py - This is the script that tweets the top (N/2) games for the day to twitter.  If you use this script, you'll have to change the OAUTH/Secret Key information to access your twitter feed.

3) GA_Funs.py - The genetic algorithm functions are kept here. (Create Population, Get Fitness, Get Schedule Stats, Mutate Individual, Create Child)

4) Webstats_Funs.py - Houses all the webscrapping functions to get the schedule, outcomes, player and team statistics, injury information, and online betting odds.

Overview of Method:
===================
TBD

Current Speed Statistics:
=========================
TBD

Current Accuracy Statistics:
============================
TBD
