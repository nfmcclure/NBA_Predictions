################################################################
# Name:        NBA_Driver.py
# Date:        2014-10-26
# Description: Script to run and tweet NBA Predictions
#
# Author:      Nick McClure (nfmcclure@gmail.com)
#
#
################################################################

import pandas as pd
import numpy as np
import GA_Funs
import datetime
import Webstats_Funs
import os
import sqlite3
from datetime import datetime, timedelta
import timeit
import matplotlib.pyplot as plt
import re
import logging

wd = 'C:\\Users\\Nicholas\\PycharmProjects\\NBA_Predictions'
os.chdir(wd)

######
# Set Parameters:
"""
days_predict: How many days out to predict
year: Current year (Spring of NBA season)
N_gen: Number of generations to run
N_pop: Number of individuals in solution population
p_stat_indices: Player stat indices
t_stat_indices: Team stat indices
health_index: Which index indicates player health status
top_selection: How much % of top population to keep
mutation_p: Mutation Probability
"""
days_predict = 8
year = 2015
N_gen = 50 #50
N_pop = 75 #75
team_cols1 = range(1, 23)
team_cols2 = range(5, 19)
player_cols1 = range(1, 26)
player_cols2 = range(5, 22)
player_char_num = len(player_cols1) + len(player_cols2)
team_char_num = len(team_cols1) + len(team_cols2)
schedule_char_num = 3
health_index = 43
top_selection = 0.25
mutation_p = 3/(player_char_num + team_char_num + schedule_char_num)
Cr_yr = year%1000  # Get 2 digit year
today = datetime.today().strftime("%Y-%m-%d")
yesterday = datetime.now() - timedelta(days=1)
yesterday = yesterday.strftime("%Y-%m-%d")

######
# Set Logging Information
log_filename = wd + '\\NBA_GA_log' + today.replace('-','') + '.log'
logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s : %(message)s')

logging.info('Starting NBA GA Prediction')
logging.info('days_predict = %s', days_predict)
logging.info('year = %s', year)
logging.info('N_gen = %s', N_gen)
logging.info('N_pop = %s', N_pop)
logging.info('top_selection = %s', top_selection)
logging.info('mutation_p = %s', mutation_p)
logging.info('today = %s', today)

######
# Perform web scrapers
year = 2015

team_site1 = "http://www.basketball-reference.com/play-index/tsl_finder.cgi?"\
             "request=1&match=single&type=team_per_game&lg_id=&year_min="+str(year)+"&year_max="+str(year)+\
             "&franch_id=&c1stat=&c1comp=gt&c1val=&c2stat=&c2comp=gt&c2val=&c3stat=&c3comp=gt&c3val=&c4stat=" \
             "&c4comp=gt&c4val=&order_by=team_name&order_by_asc=Y"
team_site2 = "http://www.basketball-reference.com/play-index/tsl_finder.cgi?"\
             "request=1&match=single&type=advanced&lg_id=&year_min="+str(year)+"&year_max="+str(year)+\
             "&franch_id=&c1stat=&c1comp=gt&c1val=&c2stat=&c2comp=gt&c2val=&c3stat=&c3comp=gt&c3val=&c4stat=" \
             "&c4comp=gt&c4val=&order_by=team_name&order_by_asc=Y"

player_site1 = "http://www.basketball-reference.com/play-index/psl_finder.cgi?request=1&match=single&type="\
               "totals&per_minute_base=36&lg_id=&is_playoffs=N&year_min="+str(year)+"&year_max="+str(year)+\
               "&franch_id=&season_start=1&season_end=-1&age_min=0&age_max=99&height_min=0&height_max=99&"\
               "birth_country_is=Y&birth_country=&is_active=Y&is_hof=&is_as=&as_comp=gt&as_val=&pos_is_g=Y&"\
               "pos_is_gf=Y&pos_is_f=Y&pos_is_fg=Y&pos_is_fc=Y&pos_is_c=Y&pos_is_cf=Y&qual=&c1stat=&c1comp="\
               "gt&c1val=&c2stat=&c2comp=gt&c2val=&c3stat=&c3comp=gt&c3val=&c4stat=&c4comp=gt&c4val=&c5stat="\
               "&c5comp=gt&c6mult=1.0&c6stat=&order_by=player&order_by_asc=Y"

player_site2 = "http://www.basketball-reference.com/play-index/psl_finder.cgi?request=1&match=single&"\
               "per_minute_base=36&type=advanced&lg_id=&is_playoffs=N&year_min="+str(year)+"&year_max="+str(year)+\
               "&franch_id=&season_start=1&season_end=-1&age_min=0&age_max=99&height_min=0&height_max=99&"\
               "birth_country_is=Y&birth_country=&is_active=Y&is_hof=&is_as=&as_comp=gt&as_val=&pos_is_g=Y&"\
               "pos_is_gf=Y&pos_is_f=Y&pos_is_fg=Y&pos_is_fc=Y&pos_is_c=Y&pos_is_cf=Y&qual=&c1stat=&c1comp=gt&"\
               "c1val=&c2stat=&c2comp=gt&c2val=&c3stat=&c3comp=gt&c3val=&c4stat=&c4comp=gt&c4val=&c5stat=&"\
               "c5comp=gt&c6mult=1.0&c6stat=&order_by=player&order_by_asc=Y"

schedule_site = "http://www.basketball-reference.com/leagues/NBA_"+str(year)+"_games.html"

health_site = "http://espn.go.com/nba/injuries"

odds_site = "http://espn.go.com/nba/lines"

team_data1_labels = ['rank','games','wins','losses','win_loss_per','mp','fg','fga','two_p','two_pa','three_p',
                     'three_pa','ft','fta','orb','drb','trb','ast','stl','blk','tov','pf','pts']
team_data2_labels = ['rank','games','wins','losses','win_loss_per','mov','sos','srs','pace','ortg','drtg','efg_per',
                     'tov_per','orb_per','ft_fga','efg_per_opp','tov_per_opp','orb_per_opp','ft_fga_opp']

player_data1_labels = ['rank','age','games','games_started','min_played','fg','fga','two_p','two_pa','three_p',
                       'three_pa','ft','fta','orb','drb','trb','ast','stl','blk','tov','pf','pts','fg_per',
                       'two_p_per','three_p_per','ft_per']
player_data2_labels = ['rank','age','games','games_started','min_played','per','ts_per','efg_per','orb_per','drb_per',
                       'trb_per','ast_per','stl_per','blk_per','tov_per','usg_per','ortg2','drtg2','ows','dws','ws',
                       'ws_48','fg_per','two_p_per','three_p_per','ft_per']

logging.info('Performing Web-scrapes')
team_data1 = Webstats_Funs.get_team_stats(site=team_site1, headers=team_data1_labels)
team_data1['update_date'] = today
team_data2 = Webstats_Funs.get_team_stats(site=team_site2, headers=team_data2_labels)
team_data2['update_date'] = today
player_data1 = Webstats_Funs.get_player_stats(site=player_site1, headers=player_data1_labels)
player_data1['update_date'] = today
player_data2 = Webstats_Funs.get_player_stats(site=player_site2, headers=player_data2_labels)
player_data2['update_date'] = today
health_data = Webstats_Funs.get_injury_list(site=health_site)
health_data['update_date'] = today
schedule_data = Webstats_Funs.get_schedule(site=schedule_site)
schedule_data['update_date'] = today
odds_data = Webstats_Funs.get_lines(odds_site)
odds_data['update_date'] = today

######
# Set Health status Modifications
health_data['health_mod'] = 0.75
health_data.loc[health_data['player_status'] == 'Out', 'health_mod'] = 0

######
# Find index of last game played, and remove cancelled games
played_game_indices = [i for i,e in enumerate(schedule_data['home_pts']) if e>0]

######
# Create a schedule date column
schedule_data['py_date'] = [datetime.strptime(x,"%a, %b %d, %Y") for x in schedule_data['date']]
schedule_data['days_ago'] = [(datetime.strptime(today, "%Y-%m-%d") - x).days for x in schedule_data['py_date']]

######
# Switch Schedule Names
team_name_dict = {'Los Angeles Lakers': 'LAL',
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

schedule_data = schedule_data.replace({'home': team_name_dict,
                                       'visitor': team_name_dict})

# Note the following index here is still tied to original schedule data
future_schedule = schedule_data[(max(played_game_indices)+1):]
future_schedule = future_schedule.reset_index()
schedule_data = schedule_data[schedule_data['home_pts']>0]

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
# Setup input output files
logging.info('Saving Data to Database')
data_folder = wd + '\\data\\'
saveFrameToTable(dataFrame=team_data1, tableName='team_stats1', sqldbName='NBA_data', dbFolder=data_folder, e_option='append')
saveFrameToTable(dataFrame=team_data2, tableName='team_stats2', sqldbName='NBA_data', dbFolder=data_folder, e_option='append')
saveFrameToTable(dataFrame=player_data1, tableName='player_stats1', sqldbName='NBA_data', dbFolder=data_folder, e_option='append')
saveFrameToTable(dataFrame=player_data2, tableName='player_stats2', sqldbName='NBA_data', dbFolder=data_folder, e_option='append')
saveFrameToTable(dataFrame=health_data, tableName='health_data', sqldbName='NBA_data', dbFolder=data_folder, e_option='append')
saveFrameToTable(dataFrame=odds_data, tableName='odds_data', sqldbName='NBA_data', dbFolder=data_folder, e_option='append')

######
# Create a game weight vector
#  - this will be a vector of weights to score fitness on (scaled to a sum of 1)
#  - parameters:
#    -- t1: how many days far back the scaling of highest equal weights go
#    -- t2: how many more days back the linear scaling down to zero go (zero after)
logging.info('Setting Game Weights')
t1 = 21  # (3 weeks)
t2 = 42  # (3 more weeks, so zero weight for games older than 6 weeks)

num_games_within_t1 = sum(schedule_data['days_ago'] <= t1)
num_games_within_t2 = sum((schedule_data['days_ago'] > t1) & (schedule_data['days_ago'] <= t2))
num_zero_weights = sum(schedule_data['days_ago'] > t2)

weight_list = np.repeat(0.0,(num_games_within_t1 + num_games_within_t2 + num_zero_weights))
weight_list[0:num_games_within_t1] = np.repeat(1.0,num_games_within_t1)
weight_list[num_games_within_t1:(num_games_within_t2 + num_games_within_t1)] = np.linspace(1.0, 0.0, num=num_games_within_t2)
weight_list = weight_list[::-1]
weight_list = [x/sum(weight_list) for x in weight_list]  # Normalize to sum of 1

schedule_data['weights'] = weight_list

num_games = num_games_within_t1 +  num_games_within_t2
first_weight_row = schedule_data[schedule_data['weights']>0].index.tolist()[0]

# Create the winner of previous games
def get_winner(x):
    if x['home_pts'] > x['visitor_pts']:
        return x['home']
    else:
        return x['visitor']

schedule_data['winner'] = schedule_data.apply(get_winner, axis=1)

logging.info('Saving Game Data to Database')
saveFrameToTable(dataFrame=schedule_data, tableName='schedule_data', sqldbName='NBA_data', dbFolder=data_folder, e_option='replace')

######
# Create population parameters

upper_bounds = np.repeat(1, player_char_num + team_char_num + schedule_char_num)
lower_bounds = np.repeat(-1, player_char_num + team_char_num + schedule_char_num)

######
# Create initial population
logging.info('Initializing Population')
population = GA_Funs.create_population(lower_bounds, upper_bounds, n=N_pop, type_fill='random')


######
# Assess initial fitness

fitness = np.repeat(0.0, N_pop)

for n in range(N_pop):
    fitness[n] = GA_Funs.get_fitness(population[n,], schedule_data,
                                             team_data1, team_data2, team_cols1, team_cols2,
                                             player_data1, player_data2, player_cols1, player_cols2, health_data)


######
# Start Genetic Algorithm
logging.info('Starting Genetic Algorithm')
fitness_plot_vals = np.repeat(0.0, N_gen)

for g in range(N_gen):

    tic = timeit.default_timer()

    print('Calculating Generation #' + str(g+1))
    # Order array fitness
    fitness_ordered_ind = sorted(range(len(fitness)), key=lambda k: fitness[k], reverse=True)

    # Create parent population by keeping top X% (top_selection)
    top_num = round(top_selection*N_pop)
    # parent_indices = [i for i,e in enumerate(fitness_ordered_ind) if e <= top_num]
    parent_indices = fitness_ordered_ind[:top_num]
    parent_population = population[parent_indices, :]

    num_children = len(population) - len(parent_population)
    children_pop = np.zeros(shape=(num_children,player_char_num + team_char_num + schedule_char_num))
    # Create Children
    for c in range(num_children):
        parent1 = parent_population[np.random.randint(len(parent_population), size=1)]
        parent2 = parent_population[np.random.randint(len(parent_population), size=1)]
        children_pop[c,:] = GA_Funs.get_child(parent1, parent2)
        # Mutate Children
        children_pop[c,:] = GA_Funs.mutate_individual(children_pop[c,:], mutation_p, lower_bounds, upper_bounds)

    # Combine children and parents
    population = np.vstack((parent_population, children_pop))

    # Recheck Fitness
    for n in range(N_pop):
        fitness[n] = GA_Funs.get_fitness(population[n,], schedule_data,
                                         team_data1, team_data2, team_cols1, team_cols2,
                                         player_data1, player_data2, player_cols1, player_cols2, health_data)

    # Save max fitness
    fitness_plot_vals[g] = max(fitness)
    print(max(fitness))

    # Calculate timing
    toc = timeit.default_timer()
    gen_time_seconds = toc-tic
    # Print Time Left
    hours_left = round(((toc-tic)*(N_gen-g))/3600.0)
    min_left = round(((((toc-tic)*(N_gen-g))/3600.0) % 1) * 60.0)
    print('Time Left: ' + str(hours_left) + ' hours, ' + str(min_left) + ' minutes.')
    logging.info('Generation ' + str(g+1) + '. Max Fitness is ' + str(round(max(fitness), 5)))
    logging.info('Generation calculation time: ' + str(round(gen_time_seconds,3)) + ' seconds.')


# Save max individual
max_individual = population[[i for i,e in enumerate(fitness) if e==max(fitness)], :][0]
col_names = [player_data1_labels[x] for x in player_cols1] +\
            [player_data2_labels[x] for x in player_cols2] +\
            [team_data1_labels[x] for x in team_cols1] +\
            [team_data2_labels[x] for x in team_cols2] +\
            ['home_away', 'streak', 'days_rest']
df_max_individual = pd.DataFrame(max_individual)
df_max_individual = df_max_individual.transpose()
df_max_individual.columns = col_names
df_max_individual['date'] = today
df_max_individual['fitness'] = max(fitness)
df_max_individual = df_max_individual.T.groupby(level=0).first().T
logging.info('Recording/Storing Max Individual, Fitness: ' + str(round(max(fitness), 5)))
saveFrameToTable(dataFrame=df_max_individual, tableName='max_individual', sqldbName='NBA_data', dbFolder=data_folder, e_option='append')

# Save fitness per generation
logging.info('Saving Fitness over Generations Data')
fitness_df = pd.DataFrame({'date': np.repeat(today, N_gen), 'generation': range(N_gen), 'fitness': fitness_plot_vals})
saveFrameToTable(dataFrame=fitness_df, tableName='fitness', sqldbName='NBA_data', dbFolder=data_folder, e_option='append')

# Plot fitness?
if True:
    plt.plot(fitness_plot_vals)
    plt.xlabel('Generations')
    plt.ylabel('Fitness')
    plt.title('NBA Model Fitness')
    plt.grid(True)
    plt.savefig('NBA_Fitness_' + str(today).replace('-','') + '.png')
    logging.info('Saved Fitness Chart: ' + wd + '\\NBA_Fitness_' + str(today).replace('-','') + '.png')

######
# Declare prediction function
def get_prediction(schedule_data, historic_schedule, individual, days_predict,
                   team_data1, team_data2, team_cols1, team_cols2,
                   player_data1, player_data2, player_cols1, player_cols2,
                   health_data, slope, intercept):
    # future_schedule
    predict_schedule = schedule_data[(schedule_data['days_ago'] <= 0) & (schedule_data['days_ago'] >= -days_predict)]
    num_games_loop = len(predict_schedule)
    print('Num games to predict: ' + str(num_games_loop))
    pred_winner_list = []
    home_score_pred = []
    visitor_score_pred = []
    for i in range(num_games_loop):
        team_home = predict_schedule.loc[i, 'home']
        team_visitor = predict_schedule.loc[i, 'visitor']
        game_date = predict_schedule.loc[i, 'date']

        [team_nums_home1] = np.array(team_data1[team_data1['team'] == team_home])
        [team_nums_home2] = np.array(team_data2[team_data2['team'] == team_home])
        [team_nums_visitor1] = np.array(team_data1[team_data1['team'] == team_visitor])
        [team_nums_visitor2] = np.array(team_data2[team_data2['team'] == team_visitor])

        team_nums_home = np.hstack((team_nums_home1[team_cols1], team_nums_home2[team_cols2]))
        team_nums_visitor = np.hstack((team_nums_visitor1[team_cols1], team_nums_visitor2[team_cols2]))

        player_nums_home1 = np.array(player_data1[player_data1['team'] == team_home])
        player_nums_home2 = np.array(player_data2[player_data2['team'] == team_home])
        player_nums_visitor1 = np.array(player_data1[player_data1['team'] == team_visitor])
        player_nums_visitor2 = np.array(player_data2[player_data2['team'] == team_visitor])

        player_nums_home = np.hstack((player_nums_home1[:,player_cols1], player_nums_home2[:,player_cols2]))
        player_nums_visitor = np.hstack((player_nums_visitor1[:,player_cols1], player_nums_visitor2[:,player_cols2]))

        schedule_stats_home = GA_Funs.get_schedule_stats(predict_schedule, historic_schedule,
                                                         game_date, team_home, future_logical=True)

        schedule_stats_visitor = GA_Funs.get_schedule_stats(predict_schedule, historic_schedule,
                                                            game_date, team_visitor, future_logical=True)

        player_indices = range(len(player_cols1) + len(player_cols2))
        team_indices = range(len(player_indices), len(team_cols1) + len(team_cols2) + len(player_indices))
        schedule_indices = range(len(team_indices) + len(player_indices), len(individual))

        health_mod_home = []
        for x in player_data1['name'][player_data1['team'] == team_home]:
            if x in list(health_data['name']):
                health_mod_home.extend(health_data.loc[health_data['name']==x,'health_mod'])
            else:
                health_mod_home.extend([1.0])

        health_mod_visitor = []
        for x in player_data1['name'][player_data1['team'] == team_visitor]:
            if x in list(health_data['name']):
                health_mod_visitor.extend(health_data.loc[health_data['name']==x,'health_mod'])
            else:
                health_mod_visitor.extend([1.0])

        home_num = np.mean(np.array(player_nums_home).dot(individual[player_indices]) * health_mod_home) + \
            np.array(team_nums_home).dot(individual[team_indices]) + \
            np.array(schedule_stats_home).dot(individual[schedule_indices])

        visitor_num = np.mean(np.array(player_nums_visitor).dot(individual[player_indices]) * health_mod_visitor) + \
            np.array(team_nums_visitor).dot(individual[team_indices]) + \
            np.array(schedule_stats_visitor).dot(individual[schedule_indices])

        if visitor_num > home_num:
            pred_winner = team_visitor
        else:
            pred_winner = team_home

        pred_winner_list.append(pred_winner)
        temp_home_score = slope * home_num + intercept
        temp_visitor_score = slope * visitor_num + intercept
        home_score_pred.append(temp_home_score)
        visitor_score_pred.append(temp_visitor_score)

        pred_frame = pd.DataFrame({'winner': pred_winner_list, 'home_score_pred': home_score_pred,
                                   'visitor_score_pred': visitor_score_pred})

    return pred_frame

######
# Declare get_GA_nums function to retrieve GA nums
def get_GA_nums(schedule_data, individual,
                   team_data1, team_data2, team_cols1, team_cols2,
                   player_data1, player_data2, player_cols1, player_cols2, health_data):
    num_games_loop = len(schedule_data)
    print('Num games to predict: ' + str(num_games_loop))
    home_ga_nums = []
    visitor_ga_nums = []
    home_pts = []
    visitor_pts = []
    for i in range(num_games_loop):
        team_home = schedule_data.loc[i, 'home']
        team_visitor = schedule_data.loc[i, 'visitor']
        game_date = schedule_data.loc[i, 'date']

        [team_nums_home1] = np.array(team_data1[team_data1['team'] == team_home])
        [team_nums_home2] = np.array(team_data2[team_data2['team'] == team_home])
        [team_nums_visitor1] = np.array(team_data1[team_data1['team'] == team_visitor])
        [team_nums_visitor2] = np.array(team_data2[team_data2['team'] == team_visitor])

        team_nums_home = np.hstack((team_nums_home1[team_cols1], team_nums_home2[team_cols2]))
        team_nums_visitor = np.hstack((team_nums_visitor1[team_cols1], team_nums_visitor2[team_cols2]))

        player_nums_home1 = np.array(player_data1[player_data1['team'] == team_home])
        player_nums_home2 = np.array(player_data2[player_data2['team'] == team_home])
        player_nums_visitor1 = np.array(player_data1[player_data1['team'] == team_visitor])
        player_nums_visitor2 = np.array(player_data2[player_data2['team'] == team_visitor])

        player_nums_home = np.hstack((player_nums_home1[:,player_cols1], player_nums_home2[:,player_cols2]))
        player_nums_visitor = np.hstack((player_nums_visitor1[:,player_cols1], player_nums_visitor2[:,player_cols2]))

        schedule_stats_home = GA_Funs.get_schedule_stats(schedule_data, schedule_data,
                                                         game_date, team_home, future_logical=False)

        schedule_stats_visitor = GA_Funs.get_schedule_stats(schedule_data, schedule_data,
                                                            game_date, team_visitor, future_logical=False)

        player_indices = range(len(player_cols1) + len(player_cols2))
        team_indices = range(len(player_indices), len(team_cols1) + len(team_cols2) + len(player_indices))
        schedule_indices = range(len(team_indices) + len(player_indices), len(individual))

        health_mod_home = []
        for x in player_data1['name'][player_data1['team'] == team_home]:
            if x in list(health_data['name']):
                health_mod_home.extend(health_data.loc[health_data['name']==x,'health_mod'])
            else:
                health_mod_home.extend([1.0])

        health_mod_visitor = []
        for x in player_data1['name'][player_data1['team'] == team_visitor]:
            if x in list(health_data['name']):
                health_mod_visitor.extend(health_data.loc[health_data['name']==x,'health_mod'])
            else:
                health_mod_visitor.extend([1.0])

        home_num = np.mean(np.array(player_nums_home).dot(individual[player_indices]) * health_mod_home) + \
            np.array(team_nums_home).dot(individual[team_indices]) + \
            np.array(schedule_stats_home).dot(individual[schedule_indices])

        visitor_num = np.mean(np.array(player_nums_visitor).dot(individual[player_indices]) * health_mod_visitor) + \
            np.array(team_nums_visitor).dot(individual[team_indices]) + \
            np.array(schedule_stats_visitor).dot(individual[schedule_indices])

        home_ga_nums.extend([home_num])
        visitor_ga_nums.extend([visitor_num])
        home_pts.extend([schedule_data.loc[i, 'home_pts']])
        visitor_pts.extend([schedule_data.loc[i, 'visitor_pts']])

    point_num_data = pd.DataFrame({'home_score': home_pts, 'visitor_score': visitor_pts,
                                   'home_ga_num': home_ga_nums, 'visitor_ga_num': visitor_ga_nums})

    return point_num_data

logging.info('Getting GA Nums')
point_num_data = get_GA_nums(schedule_data, max_individual,
                   team_data1, team_data2, team_cols1, team_cols2,
                   player_data1, player_data2, player_cols1, player_cols2, health_data)

x_pts = list(point_num_data['home_ga_num'])
x_pts.extend(list(point_num_data['visitor_ga_num']))
y_pts = list(point_num_data['home_score'])
y_pts.extend(list(point_num_data['visitor_score']))

logging.info('Creating Linear Model')

x_pts = np.array(x_pts)
y_pts = np.array(y_pts)
A = np.array([x_pts,np.ones(len(x_pts))])
params = np.linalg.lstsq(A.T,y_pts)[0]
line = params[0] * x_pts + params[1]

# Generate predictions
logging.info('Generating Predictions')
pred_winner_list = get_prediction(future_schedule, schedule_data, max_individual, days_predict,
                                  team_data1, team_data2, team_cols1, team_cols2,
                                  player_data1, player_data2, player_cols1, player_cols2,
                                  health_data, params[0], params[1])

future_schedule = future_schedule[(future_schedule['days_ago'] <= 0) & (future_schedule['days_ago'] >= -days_predict)]
future_schedule = pd.concat([future_schedule, pred_winner_list], axis = 1)
saveFrameToTable(dataFrame=future_schedule, tableName='future_schedule',
                 sqldbName='NBA_data', dbFolder=data_folder, e_option='append')
logging.info('Saved Predictions')
logging.info('Done!')
