import numpy as np
import matplotlib as matplotlib
import matplotlib.pyplot as plt
import pandas as pd

def get_max_drawdown(prices):
    roll_max = prices.cummax()
    daily_drawdown = prices / roll_max - 1.0
    max_daily_drawdown = daily_drawdown.cummin()
    return max_daily_drawdown.min() * 100

def get_profit_factor(trades):
    wins = [trade.profit for trade in trades if trade.profit > 0]
    losses = [trade.profit for trade in trades if trade.profit < 0]
    total_wins = sum(wins)
    total_losses = -sum(losses)
    if total_losses > total_wins: return np.nan
    return total_wins / total_losses
