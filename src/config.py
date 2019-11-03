"""
config.py

Date: 2019-10-18

Author: nfmcclure@gmail.com

"""
import json
from datetime import datetime, timedelta

yesterday = datetime.now() - timedelta(days=1)
yesterday = yesterday.strftime("%Y-%m-%d")

config = {
    'days_predict': 8,
    'year': 2018,
    'N_gen': 50,
    'N_pop': 75,
    'team_cols1': range(1, 23),
    'team_cols2': range(5, 19),
    'player_cols1': range(1, 26),
    'player_cols2': range(5, 22),
    'schedule_char_num': 3,
    'health_index': 43,
    'top_selection': 0.25,
    'today': datetime.today().strftime("%Y-%m-%d"),
    'yesterday': yesterday,
    "team_data1_labels": ['season', 'team', 'league', 'games', 'wins', 'losses', 'win_loss_per', 'mp', 'fg', 'fga',
                          'two_p', 'two_pa', 'three_p', 'three_pa', 'ft', 'fta', 'orb', 'drb', 'trb', 'ast', 'stl',
                          'blk', 'tov', 'pf', 'pts'],
    "team_data2_labels": ['season', 'team', 'league', 'games', 'wins', 'losses', 'win_loss_per', 'mov', 'sos', 'srs',
                          'pace', 'ortg', 'drtg', 'efg_per', 'tov_per', 'orb_per', 'ft_fga', 'efg_per_opp',
                          'tov_per_opp', 'orb_per_opp', 'ft_fga_opp'],
    "player_data1_labels": ['season', 'age', 'team', 'league', 'player', 'games', 'games_started', 'min_played', 'fg',
                            'fga', 'two_p', 'two_pa', 'three_p', 'three_pa', 'ft', 'fta', 'orb', 'drb', 'trb', 'ast',
                            'stl', 'blk', 'tov', 'pf', 'pts', 'fg_per', 'two_p_per', 'three_p_per', 'e_fg_per',
                            'ft_per', 'ts_per'],
    "player_data2_labels": ['season', 'age', 'team', 'league', 'player', 'games', 'games_started', 'min_played', 'per',
                            'three_pa_r', 'ft_r', 'orb_per', 'drb_per', 'trb_per', 'ast_per', 'stl_per', 'blk_per',
                            'tov_per', 'usg_per', 'ortg', 'drtg', 'ows', 'dws', 'ws', 'ws_48', 'obpm', 'dbpm', 'bpm',
                            'vorp'],
}

config.update({
    'cr_yr': config['year'] % 1000,
    'player_char_num': len(config["player_data1_labels"]) + len(config["player_data2_labels"]),
    'team_char_num': len(config["team_data1_labels"]) + len(config["team_data2_labels"]),
})

config.update({
    'mutation_p': 3/(config['player_char_num'] + config['team_char_num'] + config['schedule_char_num']),
})

config.update({
    'team_name_dict': {'Los Angeles Lakers': 'LAL',
                       'Houston Rockets': 'HOU',
                       'New Orleans Pelicans': 'NOP',
                       'San Antonio Spurs': 'SAS',
                       'Boston Celtics': 'BOS',
                       'Orlando Magic': 'ORL',
                       'Denver Nuggets': 'DEN',
                       'Brooklyn Nets': 'BRK',
                       'Charlotte Hornets': 'CHO',
                       'Milwaukee Bucks': 'MIL',
                       'Detroit Pistons': 'DET',
                       'Philadelphia 76ers': 'PHI',
                       'Indiana Pacers': 'IND',
                       'Memphis Grizzlies': 'MEM',
                       'Minnesota Timberwolves': 'MIN',
                       'Miami Heat': 'MIA',
                       'Washington Wizards': 'WAS',
                       'New York Knicks': 'NYK',
                       'Chicago Bulls': 'CHI',
                       'Phoenix Suns': 'PHO',
                       'Portland Trail Blazers': 'POR',
                       'Oklahoma City Thunder': 'OKC',
                       'Golden State Warriors': 'GSW',
                       'Sacramento Kings': 'SAC',
                       'Toronto Raptors': 'TOR',
                       'Atlanta Hawks': 'ATL',
                       'Cleveland Cavaliers': 'CLE',
                       'Dallas Mavericks': 'DAL',
                       'Utah Jazz': 'UTA',
                       'Los Angeles Clippers': 'LAC'}
})

with open('secrets.json', 'r') as json_conn:
    json_dict = json.load(json_conn)

config.update(json_dict)
