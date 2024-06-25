#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 13:53:48 2024

Strategy 4: Intraday Renko MACD

@author: Muykheng Long
"""
import pandas as pd
import numpy as np
import datetime
import copy
from stocktrends import Renko
import yfinance as yf
import statsmodels.api as sm


def MACD(DF,a=12,b=26,c=9):
    df = DF.copy()
    df['ma_fast'] = df['Adj Close'].ewm(span=a,min_periods=a).mean()
    df['ma_slow'] = df['Adj Close'].ewm(span=b,min_periods=b).mean()
    df['macd'] = df['ma_fast'] - df['ma_slow']
    df['signal'] = df['macd'].ewm(span=c,min_periods=c).mean()
    return df['macd'],df['signal']

def ATR(DF, n=14):
    df = DF.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = df['High'] - df['Adj Close'].shift(1)
    df['L-PC'] = df['Low'] - df['Adj Close'].shift(1)
    df['TR'] = df[['H-L','H-PC','L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(n).mean()
    #   df['ATR'] = df['TR'].ewm(com=n, min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2['ATR']

def slope(ser, n):
    "function to calculate slope of n consecutive points on a plot"
    slopes = [i*0 for i in range(n-1)]
    for i in range(n, len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        x_scaled = sm.add_constant(x_scaled)
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        slopes.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
    return slope_angle

def renko_DF(DF):
    df = DF.copy()
    df.reset_index(inplace=True)
    df = df.iloc[:,[0,1,2,3,4,6]]
    df.columns = ['date','open','high','low','close','volume']
    df2 = Renko(df)
    df2.brick_size = max(.5, round(ATR(DF,120).iloc[-1],0))
    renko_df = df2.get_ohlc_data()
    renko_df['bar_num'] = np.where(renko_df['uptrend']==True,1,np.where(renko_df['uptrend']==False,-1,0))
    for i in range(1,len(renko_df['bar_num'])):
        if renko_df['bar_num'][i] > 0 and renko_df['bar_num'][i-1] > 0:
            renko_df['bar_num'][i] += renko_df['bar_num'][i-1]
        elif renko_df['bar_num'][i] < 0 and renko_df['bar_num'][i-1] < 0:
            renko_df['bar_num'][i] += renko_df['bar_num'][i-1]
    renko_df.drop_duplicates(subset='date',keep='last',inplace=True)
    return renko_df

def CAGR(DF):
    df = DF.copy()
    df['cum_return'] = (1+df['ret']).cumprod()
    n = len(df)/(252*78)
    CAGR = (df['cum_return'].iloc[-1])**(1/n)-1
    return CAGR

def volatility(DF):
    df = DF.copy()
#    df['ret'] = df['Close'].pct_change()
    vol = df['ret'].std() * np.sqrt(252*78)
    return vol

def sharpe(DF, rf):
    sharpe = (CAGR(DF) - rf)/volatility(DF)
    return sharpe    

def max_dd(DF):
    df = DF.copy()
    df['cum_return'] = (1+df['ret']).cumprod()
    df['cum_rolling_max'] = df['cum_return'].max()
    df['drawdown'] = df['cum_rolling_max'] - df['cum_return']
    return (df['drawdown']/ df['cum_rolling_max']).max()

# Download data
tickers = ['MSFT','AAPL','META','AMZN','INTC','CSCO','VZ','IBM','TSLA','AMD'] 

ohlc_intraday = {}

for ticker in tickers: 
    temp = yf.download(ticker,period='1mo',interval='5m')
    temp.dropna(how='any',inplace=True)
    ohlc_intraday[ticker] = temp
    
# Merge renko df with original ohlc df
ohlc_renko = {}
df = copy.deepcopy(ohlc_intraday)
tickers_signal = {}
tickers_ret = {}

for ticker in tickers:
    print(f'merging for {ticker}')
    renko = renko_DF(df[ticker])
    df[ticker]['date'] = df[ticker].index
    ohlc_renko[ticker] = df[ticker].merge(renko.loc[:,['date','bar_num']],how='outer',on='date')
    ohlc_renko[ticker]['bar_num'].fillna(method='ffill',inplace=True)
    ohlc_renko[ticker]['macd'] = MACD(ohlc_renko[ticker],12,26,9)[0]
    ohlc_renko[ticker]['macd_sig'] = MACD(ohlc_renko[ticker],12,26,9)[1]
    ohlc_renko[ticker]['macd_slope'] = slope(ohlc_renko[ticker]['macd'], 5) 
    ohlc_renko[ticker]['macd_sig_slope'] = slope(ohlc_renko[ticker]['macd_sig'], 5) 
    tickers_signal[ticker] = ''
    tickers_ret[ticker] = []

# Identify signals and calculate daily return
for ticker in tickers:
    print(f'calculating returns for {ticker}')
    for i in range(len(ohlc_intraday[ticker])):
        ### Check if there is no current trading signal for the ticker
        if tickers_signal[ticker] == '':
            ### Append a return of 0 for this day (no position taken)
            tickers_ret[ticker].append(0)
            if i > 0: 
                ### Check for a Buy signal
                # Conditions for a Buy signal:
                # 1. The Renko bar count must be 2 or higher (indicating strong upward momentum).
                # 2. The MACD value must be above its signal line.
                # 3. The slope of the MACD must be above the slope of the MACD signal line (indicating increasing momentum).
                if (ohlc_renko[ticker]['bar_num'][i] >= 2 and ohlc_renko[ticker]['macd'][i] > ohlc_renko[ticker]['macd_sig'][i] and ohlc_renko[ticker]['macd_slope'][i] > ohlc_renko[ticker]['macd_sig_slope'][i]):
                    tickers_signal[ticker] = 'Buy'
                ### Check for a Sell signal
                # Conditions for a Sell signal:
                # 1. The Renko bar count must be -2 or lower (indicating strong downward momentum).
                # 2. The MACD value must be below its signal line.
                # 3. The slope of the MACD must be below the slope of the MACD signal line (indicating decreasing momentum).
                elif (ohlc_renko[ticker]['bar_num'][i] <= -2 and ohlc_renko[ticker]['macd'][i] < ohlc_renko[ticker]['macd_sig'][i] and ohlc_renko[ticker]['macd_slope'][i] < ohlc_renko[ticker]['macd_sig_slope'][i]):
                    tickers_signal[ticker] = 'Sell'
        
        ### If the current signal is 'Buy'
        elif tickers_signal[ticker] == 'Buy':
            ### Calculate and append the daily return from last period
            tickers_ret[ticker].append((ohlc_renko[ticker]['Adj Close'][i]/ohlc_renko[ticker]['Adj Close'][i-1])-1)
            if i > 0: 
                ### Switch to 'Sell' if:
                # 1. The Renko bar count drops to -2 or lower
                # 2. The MACD falls below the signal line
                # 3. The slope of MACD is also below the signal line's slope
                if (ohlc_renko[ticker]['bar_num'][i] <= -2 and ohlc_renko[ticker]['macd'][i] < ohlc_renko[ticker]['macd_sig'][i] and ohlc_renko[ticker]['macd_slope'][i] < ohlc_renko[ticker]['macd_sig_slope'][i]):
                    tickers_signal[ticker] = 'Sell'
                ### End 'Buy' if MACD conditions reverse without reaching 'Sell' trigger
                elif (ohlc_renko[ticker]['macd'][i] < ohlc_renko[ticker]['macd_sig'][i] and ohlc_renko[ticker]['macd_slope'][i] < ohlc_renko[ticker]['macd_sig_slope'][i]):
                    tickers_signal[ticker] = ''
        
        ### If the current signal is 'Sell'
        elif tickers_signal[ticker] == 'Sell':
            ### Calculate and append the daily return from last period
            tickers_ret[ticker].append((ohlc_renko[ticker]['Adj Close'][i]/ohlc_renko[ticker]['Adj Close'][i-1])-1)
            if i > 0: 
                ### Switch to 'Buy' if:
                # 1. The Renko bar count rises to 2 or higher
                # 2. The MACD rises above the signal line
                # 3. The slope of MACD is also above the signal line's slope
                if (ohlc_renko[ticker]['bar_num'][i] >= 2 and ohlc_renko[ticker]['macd'][i] > ohlc_renko[ticker]['macd_sig'][i] and ohlc_renko[ticker]['macd_slope'][i] > ohlc_renko[ticker]['macd_sig_slope'][i]):
                    tickers_signal[ticker] = 'Buy'
                ### End 'Sell' if MACD conditions reverse without reaching 'Buy' trigger
                elif (ohlc_renko[ticker]['macd'][i] > ohlc_renko[ticker]['macd_sig'][i] and ohlc_renko[ticker]['macd_slope'][i] > ohlc_renko[ticker]['macd_sig_slope'][i]):
                    tickers_signal[ticker] = ''
    ohlc_renko[ticker]['ret'] = np.array(tickers_ret[ticker])
    
# Calculate overall strategy's KPIs 
strategy_df = pd.DataFrame()
for ticker in tickers: 
    strategy_df[ticker] = ohlc_renko[ticker]['ret']
strategy_df['ret'] = strategy_df.mean(axis=1)
CAGR(strategy_df)
sharpe(strategy_df, 0.05)
max_dd(strategy_df)

    
    
