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
import datetime
import numpy as np
import pandas as pd
from neo4j import GraphDatabase

from src import GA_Funs, Webstats_Funs
from datetime import datetime, timedelta

import matplotlib.pyplot as plt

pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 25)
pd.set_option('display.width', 300)