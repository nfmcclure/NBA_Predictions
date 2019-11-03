"""
Name: __main__.py
Author: Nick McClure, nfmcclure@gmail.com
Purpose: Run the NBA Prediction sequence:
 1. Download data and store it.
 2. Perform validation and ETL on data.
 3. Train Predictive model for games.
 4. Produce Validation/Test metrics.
 5. Store model and metrics.
 6. Calculate the best opportunities with online betting odds.
 7. (optional) Save/Tweet out N-betting opportunities in order of best to worst.
"""
import os
import re
import timeit
import logging
import numpy as np
import pandas as pd

from src import GA_Funs, utils
from resources import website_sources
from src.config import config

import matplotlib.pyplot as plt

pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 25)
pd.set_option('display.width', 300)

if __name__ == "__main__":
    # Load parameters, files, directories
    days_predict = config['days_predict']
    year = config['year']
    N_gen = config['N_gen']
    N_pop = config['N_pop']
    team_cols1 = config['team_cols1']
    team_cols2 = config['team_cols2']
    player_cols1 = config['player_cols1']
    player_cols2 = config['player_cols2']
    schedule_char_num = config['schedule_char_num']
    health_index = config['health_index']
    top_selection = config['top_selection']
    today = config['today']
    yesterday = config['yesterday']
    team_data1_labels = config['team_data1_labels']
    team_data2_labels = config['team_data2_labels']
    player_data1_labels = config['player_data1_labels']
    player_data2_labels = config['player_data2_labels']
    cr_yr = config['cr_yr']
    player_char_num = config['player_char_num']
    team_char_num = config['team_char_num']
    mutation_p = config['mutation_p']
    team_name_dict = config['team_name_dict']

    # Setup Logger
    if not os.path.exists('logs'):
        os.makedirs('logs')
    log_filename = os.path.join('logs', 'NBA_log_' + today.replace('-', '') + '.log')
    logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s : %(message)s')

    logging.info('Starting NBA Prediction Program')
    logging.info('With the following configuration parameters:')
    for k, v in config.items():
        if isinstance(v, dict):
            logging.info('{} :'.format(k))
            for k1, v1 in v.items():
                logging.info('{} - {}: {}'.format(k, k1, v1))
        else:
            logging.info('{}: {}'.format(k, v))

    # Load reference websites (Needs year variable, because 'year' is part of the URLs, 2018, 2019, etc...)
    logging.info('Returning websites for year: {}'.format(year))
    websites = website_sources.return_websites(year)

    # Load data
    #    - This sets up a dictionary of pandas data frames.
    #    - with keys: ['team1', 'team2', 'player1', 'player2', 'health', 'schedule', 'future_schedule, 'odds'],
    #      each one a data frame
    logging.info('Retrieving the data required.')
    data = utils.get_data(websites, today)

    ######
    # Store data in a sqlite3-database
    for name, df_val in data.items():
        utils.save_frame2table(data_frame=df_val,
                               table_name=name,
                               sqldb_name='nba_db.db',
                               db_folder='resources',
                               e_option='append')
    # Store data in cloud provider
    # TODO: Research which cloud DB to use and implement it.

    ######
    # Create a game weight vector
    #  - this will be a vector of weights to score fitness on (scaled to a sum of 1)
    #  - parameters:
    #    -- t1: how many days far back the scaling of highest equal weights go
    #    -- t2: how many more days back the linear scaling down to zero go (zero after)
    logging.info('Setting Game Weights')
    t1 = 21  # (Last 3 weeks of games equally weighted)
    t2 = 42  # (3 more weeks, so zero weight for games older than 6 weeks)

    schedule_data = data['schedule'].copy()
    num_games_within_t1 = sum(schedule_data['days_ago'] <= t1)
    num_games_within_t2 = sum((schedule_data['days_ago'] > t1) & (data['schedule']['days_ago'] <= t2))
    num_zero_weights = sum(schedule_data['days_ago'] > t2)

    weight_list = np.repeat(0.0, (num_games_within_t1 + num_games_within_t2 + num_zero_weights))
    weight_list[0:num_games_within_t1] = np.repeat(1.0, num_games_within_t1)
    weight_list[num_games_within_t1:(num_games_within_t2 + num_games_within_t1)] = np.linspace(1.0, 0.0,
                                                                                               num=num_games_within_t2)
    weight_list = weight_list[::-1]
    weight_list = [x / sum(weight_list) for x in weight_list]  # Normalize to sum of 1

    schedule_data['weights'] = weight_list

    num_games = num_games_within_t1 + num_games_within_t2
    first_weight_row = schedule_data[schedule_data['weights'] > 0].index.tolist()[0]

    # Get Winner
    schedule_data['winner'] = schedule_data.apply(utils.get_winner, axis=1)
    logging.info('Saving Game Data to Database')
    utils.save_frame2table(data_frame=schedule_data,
                           table_name='schedule',
                           sqldb_name='nba_db.db',
                           db_folder='resources',
                           e_option='replace')

