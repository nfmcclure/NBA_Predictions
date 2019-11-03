"""
utils.py

Date: 2019-10-18

Purpose: Provide utility functions to NBA driver/predictions
"""
import os
import logging
import sqlite3
import pandas as pd
from datetime import datetime
from src import Webstats_Funs
from src.config import config


def get_data(websites, today_date):
    logger = logging.getLogger()
    logger.info('Performing Web-scrapes')
    team_data1 = Webstats_Funs.get_stats(site=websites['team_site1'], column_names=config['team_data1_labels'])
    team_data1['update_date'] = today_date
    team_data2 = Webstats_Funs.get_stats(site=websites['team_site2'], column_names=config['team_data2_labels'])
    team_data2['update_date'] = today_date
    player_data1 = Webstats_Funs.get_stats(site=websites['player_site1'],
                                           paginate=True,
                                           column_names=config['player_data1_labels'])
    player_data1['update_date'] = today_date
    player_data2 = Webstats_Funs.get_stats(site=websites['player_site2'],
                                           paginate=True,
                                           column_names=config['player_data2_labels'])
    player_data2['update_date'] = today_date
    health_data = Webstats_Funs.get_injury_list(site=websites['health_site'])
    health_data['update_date'] = today_date
    schedule_data = Webstats_Funs.get_schedule(site=websites['schedule_site'])
    schedule_data['update_date'] = today_date
    odds_data = Webstats_Funs.get_lines(site=websites['odds_site'])
    odds_data['update_date'] = today_date

    # Some ETL
    health_data['health_mod'] = 0.75
    health_data.loc[health_data['player_status'] == 'Out', 'health_mod'] = 0

    # Create a schedule date column
    schedule_data['py_date'] = pd.to_datetime(schedule_data['Date'], errors='coerce')
    schedule_data['days_ago'] = [(datetime.strptime(today_date, "%Y-%m-%d") - x).days for x in schedule_data['py_date']]

    # Find index of last game played, and remove cancelled games
    schedule_data['home_pts'] = pd.to_numeric(schedule_data['home_pts'], errors='coerce')
    schedule_data['visitor_pts'] = pd.to_numeric(schedule_data['visitor_pts'], errors='coerce')
    schedule_data['Attend.'] = pd.to_numeric(schedule_data['Attend.'].str.replace(',', ''), errors='coerce')
    schedule_data = schedule_data.dropna(axis=0, how='any')
    schedule_data = schedule_data.reset_index(drop=True)
    played_game_indices = [i for i, e in enumerate(schedule_data['home_pts']) if e > 0]

    # Rename teams in both the home and visitor column.
    schedule_data = schedule_data.rename({'Home/Neutral': 'home',
                                          'Visitor/Neutral': 'visitor'}, axis=1)
    schedule_data = schedule_data.replace({'home': config['team_name_dict'],
                                           'visitor': config['team_name_dict']})

    # Note the following index here is still tied to original schedule data
    future_schedule = schedule_data[(max(played_game_indices) + 1):]
    future_schedule = future_schedule.reset_index()
    schedule_data = schedule_data[schedule_data['home_pts'] > 0]

    full_data = {
        'team1': team_data1,
        'team2': team_data2,
        'player1': player_data1,
        'player2': player_data2,
        'health': health_data,
        'schedule': schedule_data,
        'future_schedule': future_schedule,
        'odds': odds_data,
    }

    return full_data


# Function to save DataFrame to sqlite-db
def save_frame2table(data_frame, table_name, sqldb_name, db_folder, e_option):
    if not os.path.exists(db_folder):
        os.makedirs(db_folder)
    conn = sqlite3.connect(os.path.join(db_folder, sqldb_name))
    print("Database created/opened successfully.")
    data_frame.to_sql(table_name, conn, if_exists=e_option, index=False)
    conn.close()


# Create the winner of previous games
def get_winner(x):
    if x['home_pts'] > x['visitor_pts']:
        return x['home']
    else:
        return x['visitor']
