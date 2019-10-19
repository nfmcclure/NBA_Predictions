"""
utils.py

Date: 2019-10-18

Purpose: Provide utility functions to NBA driver/predictions
"""
import os
import logging
from datetime import datetime
from src import Webstats_Funs, config


def get_data(websites, today_date):
    logger = logging.getLogger()
    logger.info('Performing Web-scrapes')
    team_data1 = Webstats_Funs.get_stats(site=websites['team_site1'])
    team_data1['update_date'] = today_date
    team_data2 = Webstats_Funs.get_stats(site=websites['team_site2'])
    team_data2['update_date'] = today_date
    player_data1 = Webstats_Funs.get_stats(site=websites['player_site1'], paginate=True)
    player_data1['update_date'] = today_date
    player_data2 = Webstats_Funs.get_stats(site=websites['player_site2'], paginate=True)
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
    schedule_data['py_date'] = [datetime.strptime(x, "%a, %b %d, %Y") for x in schedule_data['date']]
    schedule_data['days_ago'] = [(datetime.strptime(today_date, "%Y-%m-%d") - x).days for x in schedule_data['py_date']]

    # Find index of last game played, and remove cancelled games
    played_game_indices = [i for i, e in enumerate(schedule_data['home_pts']) if e > 0]

    # Rename teams in both the home and visitor column.
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
def saveFrameToTable(dataFrame, tableName, sqldbName, dbFolder, e_option):
    if not os.path.exists(dbFolder):
        os.makedirs(dbFolder)
    conn = sqlite3.connect(dbFolder + sqldbName + '.db')
    print("Database created/opened successfully.")
    dataFrame.to_sql(tableName, conn, flavor='sqlite', if_exists=e_option)
    conn.close()