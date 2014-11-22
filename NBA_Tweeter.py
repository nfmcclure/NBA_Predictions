################################################################
# Name:        NBA_Tweeter.py
# Date:        2014-11-19
# Description: Script to tweet top NBA Predictions
#
# Author:      Nick McClure (nfmcclure@gmail.com)
#
#
################################################################

import pandas as pd
import numpy as np
import os
import sqlite3
import Webstats_Funs
from datetime import datetime, timedelta
from pandas.io import sql
from twython import Twython

wd = 'C:\\Users\\Nicholas\\PycharmProjects\\NBA_Predictions'
os.chdir(wd)
database_file = wd + '\\data\\NBA_data.db'
data_folder = wd + '\\data\\'


######
# Function to save DataFrame to sqlite-db
def saveFrameToTable(dataFrame, tableName, sqldbName, dbFolder, e_option):
    if not os.path.exists(dbFolder):
        os.makedirs(dbFolder)
    conn = sqlite3.connect(dbFolder + sqldbName + '.db')
    print("Database created/opened successfully.")
    dataFrame.to_sql(tableName, conn, flavor='sqlite', if_exists=e_option)
    conn.close()

######
# Set up database connection
nba_data_conn = sqlite3.connect(database_file)

######
# Set up today's information
today = datetime.today().strftime("%Y-%m-%d")
yesterday = datetime.now() - timedelta(days=1)
yesterday = yesterday.strftime("%Y-%m-%d")

######
# Get current lines
odds_site = 'http://espn.go.com/nba/lines'
odds_data = Webstats_Funs.get_lines(odds_site)
odds_data['update_date'] = today
saveFrameToTable(dataFrame=odds_data, tableName='odds_data',
                 sqldbName='NBA_data', dbFolder=data_folder, e_option='append')

######
# Get today's predictions
pred_data_query = 'SELECT * FROM future_schedule WHERE days_ago = 0 AND update_date = \'' + today + '\''
today_pred_data = sql.read_sql(pred_data_query, con=nba_data_conn)

odds_data = odds_data.groupby(['home','visitor']).mean()
odds_data = odds_data.reset_index()

# Do some quick calcs
today_pred_data = today_pred_data.merge(odds_data, on=['home', 'visitor'])


advantage = []
abs_advantage = []
my_home_spread = []
for g in range(len(today_pred_data)):
    home_spread_temp = today_pred_data.loc[g, 'visitor_score_pred'] - today_pred_data.loc[g, 'home_score_pred']
    my_home_spread.append(home_spread_temp)
    abs_advantage.append(abs(home_spread_temp - today_pred_data.loc[g, 'home_spread']))
    advantage.append(home_spread_temp - today_pred_data.loc[g, 'home_spread'])

today_pred_data['advantage'] = advantage
today_pred_data['abs_advantage'] = abs_advantage
today_pred_data['my_home_spread'] = my_home_spread

num_games_tweet =len(today_pred_data)

today_pred_data = today_pred_data.sort(columns='abs_advantage', ascending=False)

today_pred_data = today_pred_data.reset_index(drop=True)

tweet_sentences = []
for g in range(int(num_games_tweet)):
    if today_pred_data.loc[g, 'advantage'] > 0:
        bet_on_team = str(today_pred_data.loc[g, 'visitor'])
        not_bet_on = str(today_pred_data.loc[g, 'home'])
    else:
        bet_on_team = str(today_pred_data.loc[g, 'home'])
        not_bet_on = str(today_pred_data.loc[g, 'visitor'])

    tweet_temp = bet_on_team + ' should cover the average online betting spread against ' + not_bet_on
    tweet_sentences.append(tweet_temp)

# EDIT BELOW FOR YOUR TWITTER API KEY INFO
APP_KEY = "APP_KEY"
APP_SECRET = "APP_SECRET"
OAUTH_TOKEN = "OAUTH_TOKEN"
OAUTH_TOKEN_SECRET = "OAUTH_TOKEN_SECRET"

today_pred_data = today_pred_data.T.drop_duplicates().T
today_pred_data = today_pred_data.drop('level_0', 1)

print(tweet_sentences)

today_pred_data['tweets'] = tweet_sentences

saveFrameToTable(dataFrame=today_pred_data, tableName='Daily_Predictions',
                 sqldbName='NBA_data', dbFolder=data_folder, e_option='append')

# Tweet!

twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

num_games_tweet_total = max(1,np.floor(num_games_tweet/2))

pre_tweet = 'Good morning from Genetic Algorithm land (v2.0)! According to my computations today,' +\
    ' there are' + str(num_games_tweet_total) + ' games with significant betting edge.'

twitter.update_status(status=pre_tweet)

today_pred_data = today_pred_data.sort(columns='abs_advantage', ascending=False)

for t in range(num_games_tweet_total):
    temp_twitter_status = today_pred_data.loc[t,'tweets']
    twitter.update_status(status=temp_twitter_status)
