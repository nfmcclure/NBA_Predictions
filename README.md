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
The idea of this project was to create a naive nba predictor.  There is very little knowledge about basketball programmed into this algorithm.  For example, many algorithms assume feature importance (E.g. Three point % is more important than the winning streak...), this is not the case for this algorithm.  No feature importances are given, and it is left up to the algorithm to find the best fit.

Here is a summary of the statistics used:
 - Player Statistics: See:  http://www.basketball-reference.com/play-index/psl_finder.cgi?lid=header_pi  for the regular and advanced statistics.
 - Team Statistics: http://www.basketball-reference.com/play-index/tsl_finder.cgi?lid=header_pi  contains the regular, per game, and advanced statistics.
 - Schedule Statistics:  These are only three statistics:  (1) Home/Away, (2) Win/Lose streak, and (3) # days off prior to game.

The player statistics are modified by the current NBA injury reserve list. Here, some injuries are worth more than others, as a rolled ankle is significantly less impactful than a play-preventing injury.

A genetic algorithm is used on a matrix function of the above statistics.  The coefficients evolve to predict the prior games as best as possible (weighting recent games higher).  After a set number of generations, the algorithm predicts out the next week.

Then for the current day, the online sports book odds are downloaded, compared and the best games to bet on are outputed for the day.

Current Speed Statistics:
=========================
TBD

Current Accuracy Statistics:
============================
TBD
