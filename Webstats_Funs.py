################################################################
# Name:        Webstats_Funs.py
# Date:        2014-10-26
# Description: Add on functions for webscraping NBA stats
#
# Author:      Nick McClure (nfmcclure@gmail.com)
#
#
################################################################

import pandas as pd
import numpy as np
import requests
from lxml import html
import re


def xnum(s,val):
    if s is None:
        return val
    return float(s)

# def xstr(s):
#     if s is None:
#         return ''
#     return str(s)


def get_team_stats(site, headers):
    page = requests.get(site)
    tree = html.fromstring(page.text)
    stats = tree.xpath('//td[@align="right"]/text()')
    stats = [float(x) for x in stats]
    stats_frame = np.array(stats).reshape(30,(len(stats)/30))
    stats_frame = pd.DataFrame(stats_frame, columns=headers)

    teams = tree.xpath('//td[@align="left"]/a[starts-with(@href,"/teams")]/text()')
    stats_frame['team'] = teams

    return stats_frame


def get_player_stats(site, headers):
    page1 = requests.get(site)
    tree1 = html.fromstring(page1.text)
    stats1 = tree1.xpath('//td[@align="right"]')
    stats1 = [x.text for x in stats1]
    stats1 = [xnum(x,0) for x in stats1]
    names1 = tree1.xpath('//td[@align="left"][@class=" highlight_text"]/a/text()')
    teams1 = tree1.xpath('//td[@align="left"]/a[starts-with(@href,"/teams")]/text()')

    text_addon = "&offset="
    seq_addon = range(100,401,100)
    for a in seq_addon:
        page_temp = requests.get(site+text_addon+str(a))
        tree_temp = html.fromstring(page_temp.text)
        stats_temp = tree_temp.xpath('//td[@align="right"]')
        stats_temp = [x.text for x in stats_temp]
        stats_temp = [xnum(x,0) for x in stats_temp]
        stats1.extend(stats_temp)
        names_temp = tree_temp.xpath('//td[@align="left"][@class=" highlight_text"]/a/text()')
        teams_temp = tree_temp.xpath('//td[@align="left"]/a[starts-with(@href,"/teams")]/text()')
        names1.extend(names_temp)
        teams1.extend(teams_temp)

    stats1 = np.array(stats1).reshape((len(stats1)/26,26))
    stats1 = pd.DataFrame(stats1, columns=headers)
    stats1['name'] = names1
    stats1['team'] = teams1
    return stats1


def get_schedule(site):
    page = requests.get(site)
    tree = html.fromstring(page.text)
    names = tree.xpath('//td[@align="left"]/a/text()')
    score_names = tree.xpath('//td[@align="right"]')
    score_names = [x.text for x in score_names]
    score_names = [xnum(x,-1) for x in score_names]
    date_list = names[0::3]
    visitor_list = names[1::3]
    home_list = names[2::3]
    visitor_score = score_names[0::2]
    home_score = score_names[1::2]
    schedule_frame = pd.DataFrame({'date': date_list,
                                   'visitor': visitor_list,
                                   'home': home_list,
                                   'visitor_pts': visitor_score,
                                   'home_pts': home_score})
    return schedule_frame


######
# Get injury reserve list
def get_injury_list(site):
    page = requests.get(site)
    tree = html.fromstring(page.text)
    names_even = tree.xpath('//tr[starts-with(@class,"evenrow player")]/td/a/text()')
    names_odd = tree.xpath('//tr[starts-with(@class,"oddrow player")]/td/a/text()')
    status_even = tree.xpath('//tr[starts-with(@class,"evenrow player")]/td/following-sibling::td/text()')
    status_even = status_even[0::2]
    status_odd = tree.xpath('//tr[starts-with(@class,"oddrow player")]/td/following-sibling::td/text()')
    status_odd = status_odd[0::2]

    names = names_even + names_odd
    status = status_even + status_odd

    injury_frame = pd.DataFrame({'name': names,
                                 'player_status': status})
    injury_frame.drop_duplicates(subset='name', inplace=True)
    injury_frame.reset_index(inplace=True, drop=True)
    return injury_frame

######
# Get current NBA Lines
def get_lines(site):
    page = requests.get(site)
    tree = html.fromstring(page.text)
    names = tree.xpath('//table/tr/td/text()')
    starter_regex = re.compile(r'[A-Z a-z]+ at [A-Z a-z]+,')
    team_groups = []
    for x in names:
        group_num = -1
        if starter_regex.match(x):
            group_num += 1
            team_groups.append([x])
        else:
            team_groups[group_num].extend([x])

    team_lines = pd.DataFrame()

    for tg in team_groups:
        home_name_list = []
        visitor_name_list = []
        home_spread_list = []
        visitor_spread_list = []
        home_name_regex = re.compile(r' at ([A-Z a-z]+),')
        visitor_name_regex = re.compile(r'([A-Z a-z]+) at ')
        spread_regex = re.compile(r'^([+-][0-9]{1,2}[.0-9]*)')
        site1 = 'BETONLINE.ag'
        site2 = '5Dimes.eu'
        site3 = 'SportsBetting.ag'
        site4 = 'BOVADA'
        site5 = 'Fantasy911.com'
        site_list = []
        v_h_spread_indicator = 1
        for t in tg:
            if home_name_regex.search(t):
                home_name_list.extend([home_name_regex.search(t).group(0)[4:-1]])
            if visitor_name_regex.search(t):
                visitor_name_list.extend([visitor_name_regex.search(t).group(0)[:-4]])
            if spread_regex.match(t):
                if v_h_spread_indicator == 0:
                    home_spread_list.extend([float(t)])
                    v_h_spread_indicator = 1
                else:
                    visitor_spread_list.extend([float(t)])
                    v_h_spread_indicator = 0
            if t == site1:
                site_list.extend(['betonline'])
            if t == site2:
                site_list.extend(['fivedimes'])
            if t == site3:
                site_list.extend(['sportsbetting'])
            if t == site4:
                site_list.extend(['bovada'])
            if t == site5:
                site_list.extend(['fantasy911'])
            if t == 'EVEN':
                home_spread_list.extend([0])
                visitor_spread_list.extend([0])
        temp_team_frame = pd.DataFrame({'home_spread': home_spread_list,
                                        'visitor_spread': visitor_spread_list,
                                        'site': site_list})
        temp_team_frame['home'] = home_name_list[0]
        temp_team_frame['visitor'] = visitor_name_list[0]
        team_lines = team_lines.append(temp_team_frame)
    team_lines = team_lines.reset_index(drop=True)

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
    team_lines = team_lines.replace({'home': team_name_dict,
                                     'visitor': team_name_dict})
    return(team_lines)
