################################################################
# Name:        Webstats_Funs.py
# Date:        2014-10-26
# Description: Add on functions for webscraping NBA stats
#
# Author:      Nick McClure (nfmcclure@gmail.com)
#
#
################################################################

import re
import requests
import logging
import numpy as np
import pandas as pd
from lxml import html
from bs4 import BeautifulSoup

from src.config import config

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def xnum(s, val):
    if s is None:
        return val
    return float(s)

# def xstr(s):
#     if s is None:
#         return ''
#     return str(s)


def get_stats(site, paginate=False, column_names=None):
    """
    :param site: String. Website HTML address for table of statistics.
    :param paginate: Logical. If results are paginated, keep getting more.
    :param column_names: Rename columns of table fetched (helps deal with duplicate column names), if not None.
    :return: pandas dataframe of team statistics.
    """
    # Get site response structure object.
    log.info('Getting Data.')
    page = requests.get(site)
    # Extract the HTML text.
    site_html = page.text
    # Convert HTML text to beautiful soup object
    soup = BeautifulSoup(site_html, features="lxml")
    # Get specific table
    table = soup.find("table", attrs={"id": "stats"})
    # Get column names
    headings = [th.get_text() for th in table.find_all("tr")[1].find_all("th")][1:]
    # Store column information into a dataframe
    data_df = pd.DataFrame(columns=headings)
    for row in table.find_all("tr")[2:]:
        temp_dict = dict(zip(headings, (td.get_text() for td in row.find_all("td"))))
        data_df = data_df.append(temp_dict, ignore_index=True)

    # Get more paginated results
    if paginate:
        log.info('Paginating through data.')
        text_addon = "&offset="
        seq_addon = range(100, 501, 100)
        for a in seq_addon:
            # Get site response structure object.
            page = requests.get(site + text_addon + str(a))
            # Extract the HTML text.
            site_html = page.text
            # Convert HTML text to beautiful soup object
            soup = BeautifulSoup(site_html)
            # Get specific table
            table = soup.find("table", attrs={"id": "stats"})
            for row in table.find_all("tr")[2:]:
                temp_dict = dict(zip(headings, (td.get_text() for td in row.find_all("td"))))
                data_df = data_df.append(temp_dict, ignore_index=True)

    # Rename some team names that have stars after
    data_df['Tm'] = data_df['Tm'].str.replace('*', '')
    # Drop spacer rows that have NA as values (remnant from HTML site)
    data_df = data_df.dropna(how='all')

    # Rename columns
    if column_names:
        data_df.columns = column_names

    return data_df


def get_schedule(site):
    """
    :param site: string. Base URL of schedule site.
    :return: Dataframe of NBA schedule with scores and stats.
    """
    month_seq = ['october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june']
    data_df = pd.DataFrame()
    for month in month_seq:
        # Get site response structure object.
        page = requests.get(site + month + '.html')
        if page.status_code == 200:
            # Extract the HTML text.
            site_html = page.text
            # Convert HTML text to beautiful soup object
            soup = BeautifulSoup(site_html, features="lxml")
            # Get specific table
            table = soup.find("table", attrs={"id": "schedule"})
            # Get column names
            headings = [th.get_text() for th in table.find_all("tr")[0].find_all("th")]
            headings[3] = 'visitor_pts'
            headings[5] = 'home_pts'
            headings[6:8] = ['temp', 'overtime']
            # Store column information into a dataframe
            for row in table.find_all("tr")[1:]:
                temp_date = [td.get_text() for td in row.find_all("th")]
                temp_row = temp_date + [td.get_text() for td in row.find_all("td")]
                temp_dict = dict(zip(headings, temp_row))
                data_df = data_df.append(temp_dict, ignore_index=True)
        else:
            log.warning('Got status code: {} for URL request: {}'.format(page.status_code, site + month + '.html'))

    # Drop strange 'box score' column.
    data_df = data_df.drop('temp', 1)

    return data_df


######
# Get injury reserve list
def get_injury_list(site):
    """
    :param site: String. URL of the nba injured reserve list.
    :return: dataframe. DF of injuries and details.
    """
    # List team names:
    teams = ['Atlanta Hawks',
             'Boston Celtics',
             'Brooklyn Nets',
             'Charlotte Hornets',
             'Chicago Bulls',
             'Cleveland Cavaliers',
             'Dallas Mavericks',
             'Denver Nuggets',
             'Detroit Pistons',
             'Golden State Warriors',
             'Houston Rockets',
             'Indiana Pacers',
             'LA Clippers',
             'Los Angeles Lakers',
             'Memphis Grizzlies',
             'Miami Heat',
             'Milwaukee Bucks',
             'Minnesota Timberwolves',
             'New Orleans Pelicans',
             'New York Knicks',
             'Oklahoma City Thunder',
             'Orlando Magic',
             'Philadelphia 76ers',
             'Phoenix Suns',
             'Portland Trail Blazers',
             'Sacremento Kings',
             'San Antonio Spurs',
             'Toronto Raptors',
             'Utah Jazz',
             'Washington Wizards']
    # Get site response structure object.
    page = requests.get(site)
    # Extract the HTML text.
    site_html = page.text
    # Convert HTML text to beautiful soup object
    soup = BeautifulSoup(site_html, "html5lib")
    # Get specific table
    table = soup.find("table", attrs={"class": "tablehead"})
    # Store column information into a dataframe
    data_df = pd.DataFrame()
    comments = []
    team_name, name, status, date = None, None, None, None
    new_name, new_status, new_date = None, None, None
    for row in table.find_all("tr"):
        text_entries = [x.get_text() for x in row.find_all('td')]
        # Determine if we have a team name, injury entry, or comment entry.
        if len(text_entries) == 1:
            if text_entries[0] in teams:
                team_name = text_entries[0]
            else:
                comments.append(text_entries[0])
        elif len(text_entries) == 3 and text_entries[0] != 'NAME':
            new_name, new_status, new_date = text_entries
        if new_name != name or new_status != status or new_date != date:
            name, status, date = new_name, new_status, new_date
            data_df = data_df.append({'Tm': team_name,
                                      'name': name,
                                      'player_status': status,
                                      'date': date}, ignore_index=True)
    # Get the max-date for each player.
    month_order = {'Oct': 0, 'Nov': 1, 'Dec': 2, 'Jan': 3, 'Feb': 4, 'Mar': 5, 'Apr': 6, 'May': 7, 'Jun': 8, 'Jul': 9}
    data_df['month'] = data_df['date'].str.slice(0, 3)
    data_df['month_order'] = data_df['month'].map(month_order)
    data_df['day'] = data_df['date'].str.split(' ').str.get(1)
    data_df['day'] = data_df['day'].apply(lambda x: '{0:0>2}'.format(x))
    data_df['date_int'] = data_df['month_order'].map(str) + data_df['day']

    # Drop un-needed columns
    data_df = data_df.drop(['date', 'month', 'month_order', 'day'], axis=1)

    # Groupby - max(date_int) to get most recent injury for each player
    idx = data_df.groupby(['Tm', 'name'])['date_int'].transform(max) == data_df['date_int']
    data_df = data_df[idx].reset_index(drop=True)

    # Drop date-int column
    data_df = data_df.drop(['date_int'], axis=1)
    return data_df

######
# Get current NBA Lines
def get_lines(site):
    """
    :param site:
    :return:
    """
    page = requests.get(site)
    if page.status_code == 200:
        # Extract the HTML text.
        site_html = page.text
        # Convert HTML text to beautiful soup object
        soup = BeautifulSoup(site_html, "html5lib")
        # Get specific table
        table = soup.find('table') # , attrs={'class': 'mod-container mod-table mod-no-header'}
        # Initialize dataframe
        headings = ['source', 'home_team', 'visitor_team',
                    'spread', 'visitor_spread_ml', 'home_spread_ml',
                    'total', 'total_over', 'total_under',
                    'home_ml', 'visitor_ml']
        data_df = pd.DataFrame(columns=headings)
        # Store column information into a dataframe
        for ix, row in enumerate(table.find_all("tr", {'class': ['oddrow', 'evenrow']})):
            temp_source = row.find_all('td')[0].get_text()

            if temp_source in ['Westgate', "Caesar's", 'William Hill', 'Wynn', 'Unibet']:

                # Get spread information
                temp_spread = row.find_all('tr')[0].find_all('td')[0].contents[0]
                temp_ml_spread = [str(x) for x in row.find_all('tr')[0].find_all('td')[1].contents if
                                  str(x) not in ['<br/>']]
                temp_team_visitor = temp_ml_spread[0].split(': ')[0]
                temp_visitor_ml_spread = temp_ml_spread[0].split(': ')[1]
                temp_team_home = temp_ml_spread[1].split(': ')[0]
                temp_home_ml_spread = temp_ml_spread[1].split(': ')[1]

                # Get total score information
                temp_total = row.find_all('tr')[1].find_all('td')[0].contents[0]
                temp_total_bets = [str(x) for x in row.find_all('tr')[1].find_all('td')[1].contents if
                                   str(x) not in ['<br/>']]
                temp_total_over = temp_total_bets[0].split(': ')[1]
                temp_total_under = temp_total_bets[1].split(': ')[1]

                # Get money-line information
                money_lines = [str(x) for x in row.find_all('td')[7].contents if str(x) not in ['<br/>']]
                temp_team_visitor2 = money_lines[0].split(': ')[0]
                temp_team_home2 = money_lines[1].split(': ')[0]
                assert temp_team_visitor == temp_team_visitor2, 'Visitor Teams do not match, {} , {}'.format(
                    temp_team_visitor, temp_team_visitor2)
                assert temp_team_home == temp_team_home2, 'Home Teams do not match, {} , {}'.format(temp_team_home,
                                                                                                    temp_team_home2)
                temp_ml_visitor = money_lines[0].split(': ')[1]
                temp_ml_home = money_lines[1].split(': ')[1]

                temp_dict = {
                    'source': temp_source,
                    'home_team': temp_team_home,
                    'visitor_team': temp_team_visitor,
                    'spread': temp_spread,
                    'visitor_spread_ml': temp_visitor_ml_spread,
                    'home_spread_ml': temp_home_ml_spread,
                    'total': temp_total,
                    'total_over': temp_total_over,
                    'total_under': temp_total_under,
                    'home_ml': temp_ml_home,
                    'visitor_ml': temp_ml_visitor
                }
                data_df = data_df.append(temp_dict, ignore_index=True)
    else:
        log.warn('Got status code: {} for URL request: {}'.format(page.status_code, site))

    team_name_dict = {'LA Lakers': 'LAL',
                  'Houston': 'HOU',
                  'New Orleans': 'NOP',
                  'San Antonio': 'SAS',
                  'Boston': 'BOS',
                  'Orlando': 'ORL',
                  'Denver': 'DEN',
                  'Brooklyn': 'BRK',
                  'Charlotte': 'CHO',
                  'Milwaukee': 'MIL',
                  'Detroit': 'DET',
                  'Philadelphia': 'PHI',
                  'Indiana': 'IND',
                  'Memphis': 'MEM',
                  'Minnesota': 'MIN',
                  'Miami': 'MIA',
                  'Washington': 'WAS',
                  'NY Knicks': 'NYK',
                  'Bulls': 'CHI',
                  'Phoenix': 'PHO',
                  'Portland': 'POR',
                  'Oklahoma City': 'OKC',
                  'Golden State': 'GSW',
                  'Sacramento': 'SAC',
                  'Toronto': 'TOR',
                  'Atlanta': 'ATL',
                  'Cleveland': 'CLE',
                  'Dallas': 'DAL',
                  'Utah': 'UTA',
                  'LA Clippers': 'LAC'}
    team_lines = data_df.replace({'home': team_name_dict, 'visitor': team_name_dict})
    return team_lines
