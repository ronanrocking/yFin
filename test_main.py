import main.fetch
import main.indicators
import private.conditions
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

# Fetch data
df = main.fetch.get_all_candles("LICHSGFIN")

print(list(private.conditions.ema_cluster_3(df, "past", 1)))
