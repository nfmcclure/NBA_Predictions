################################################################
# Name:        GA_Funs.py
# Date:        2014-10-26
# Description: Add on functions for NBA Genetic Algorithms
#
# Author:      Nick McClure (nfmcclure@gmail.com)
#
#
################################################################

import pandas as pd
import numpy as np
import numpy.random
import itertools
import random

#######
# create_population will initialize our population of solutions
def create_population(lower_bounds, upper_bounds, n=100, type_fill='random'):

    population = np.zeros(shape=(n, len(lower_bounds)))
    # Error check
    if len(lower_bounds) != len(upper_bounds):
        raise NameError('Length of Upper Bounds must equal length of Lower Bounds.')

    if type_fill == 'random':
        for i in range(n):
            temp_row = []
            for a, b in zip(lower_bounds, upper_bounds):
                temp_row.extend(np.random.uniform(a,b,1))
            population[i] = temp_row

    elif type_fill == 'normal':
        print('normal: not implemented yet')
    elif type_fill == 'integer':
        print('integer: not implemented yet')
    else:
        print('unknown creation method')

    return population

######
# Get fitness of individual
def get_fitness(individual, schedule_data,
                team_data1, team_data2, team_cols1, team_cols2,
                player_data1, player_data2, player_cols1, player_cols2, health_data):

    played_game_indices = [i for i, e in enumerate(schedule_data['home_pts']) if e > 0]

    fitness = 0

    for i in played_game_indices:

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

        schedule_stats_home = get_schedule_stats(schedule_data, schedule_data, game_date, team_home)
        schedule_stats_visitor = get_schedule_stats(schedule_data, schedule_data, game_date, team_visitor)

        player_indices = range(len(player_cols1) + len(player_cols2))
        team_indices = range(len(player_indices), len(team_cols1) + len(team_cols2) + len(player_indices))
        schedule_indices = range(len(team_indices) + len(player_indices), len(individual))

        home_num = np.mean(np.array(player_nums_home).dot(individual[player_indices]) * health_mod_home) + \
            np.array(team_nums_home).dot(individual[team_indices]) + \
            np.array(schedule_stats_home).dot(individual[schedule_indices])

        visitor_num = np.mean(np.array(player_nums_visitor).dot(individual[player_indices]) * health_mod_visitor) + \
            np.array(team_nums_visitor).dot(individual[team_indices]) + \
            np.array(schedule_stats_visitor).dot(individual[schedule_indices])

        actual_winner = schedule_data.loc[i, 'winner']

        if home_num > visitor_num:
            pred_winner = schedule_data.loc[i, 'home']
        else:
            pred_winner = schedule_data.loc[i, 'visitor']

        if actual_winner == pred_winner:
            fitness += schedule_data.loc[i, 'weights']
    return fitness


######
# Create a schedule statistics function:
#  - this will accept a single game row from scheduling and return three #s:
#    - Home (1) vs. Away (0?), Streak # (+ for winning, - for losing), and Days Rest
#  - this is great for past games (for fitness), but for future games, will be equal to current day


def get_schedule_stats(schedule_data, historic_schedule, date, team, future_logical=False):
    # Define Home/Away statistic
    if team in list(schedule_data.loc[schedule_data['py_date'] == date,'home']):
        h_a_stat = 1
    elif team in list(schedule_data.loc[schedule_data['py_date'] == date,'visitor']):
        h_a_stat = 0
    else:
        raise NameError('Team name not found in home or visitor date')

    # Define Streak Statistic
    if future_logical:
        team_schedule_data = historic_schedule[(historic_schedule['home'] == team) | (historic_schedule['visitor'] == team)]
        team_schedule_data = team_schedule_data.reset_index()

        winner_list = [1 if x == team else -1 for x in team_schedule_data['winner']]
        streak_stat = sum(1 for _ in next(itertools.groupby(winner_list[::-1]), ('ignored',()))[1])
        if winner_list[::-1][0] != team:
            streak_stat = -streak_stat
    else:
        team_schedule_data = schedule_data[(schedule_data['home'] == team) | (schedule_data['visitor'] == team)]
        team_schedule_data = team_schedule_data.reset_index()

        winner_list = [1 if x == team else -1 for x in team_schedule_data['winner']]
        streak_stat = sum(1 for _ in next(itertools.groupby(winner_list[::-1]), ('ignored',()))[1])
        if winner_list[::-1][0] != team:
            streak_stat = -streak_stat

    # Define Days Rest Statistic
    try:
        days_rest_temp = min(team_schedule_data['days_ago'][team_schedule_data['py_date'] < date]) - \
            min(team_schedule_data['days_ago'][team_schedule_data['py_date'] == date])
        days_rest_stat = min(7, days_rest_temp)
    except:
        days_rest_stat = 7

    return (h_a_stat, streak_stat, days_rest_stat)


######
# Create Mutation Function

def mutate_individual(individual, mutation_p, lower_bounds, upper_bounds):
    for g in range(len(individual)):
        if np.random.rand() <= mutation_p:
            individual[g] = np.random.uniform(lower_bounds[g],upper_bounds[g],1)
    return(individual)

######
# Create Crossover Function

def get_child(parent1, parent2):
    num_features = len(parent1)
    [crossover_pt] = random.sample(range(num_features), 1)
    progeny = np.append(parent1[0:crossover_pt],parent2[crossover_pt:num_features])
    return progeny
