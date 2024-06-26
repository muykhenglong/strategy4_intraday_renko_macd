# Intraday Renko MACD Trading Strategy

This Python script implements an intraday trading strategy using Renko charts and the Moving Average Convergence Divergence (MACD) indicator.

## Features

- **Renko Chart Calculation**: Utilizes Renko charts to filter market noise and identify trends.
- **MACD Indicator**: Employs the MACD indicator to determine the momentum and direction of stock price trends.
- **Automated Trading Signals**: Generates buy and sell signals based on the alignment of Renko and MACD readings.
- **Performance Metrics**: Calculates key performance indicators such as Compound Annual Growth Rate (CAGR), Sharpe Ratio, and Maximum Drawdown to evaluate the strategy's effectiveness.

Requirements

- Python 3.8.19
- yfinance
- stocktrends
- statsmodels

## Strategy Description
- Renko Charts: Renko charts are a type of price charting that help filter out minor price movements, focusing only on significant changes. The size of each Renko block is based on the Average True Range (ATR), making it more adaptable to market conditions. In our strategy, a new Renko block is created when the price movement exceeds the ATR-derived threshold.
- MACD Indicator: The Moving Average Convergence Divergence (MACD) is a trend-following momentum indicator that shows the relationship between two moving averages of a security’s price. The MACD is calculated by subtracting the 26-period Exponential Moving Average (EMA) from the 12-period EMA. The result of that calculation is the MACD line. A nine-day EMA of the MACD called the "signal line," is then plotted on top of the MACD line, which can function as a trigger for buy and sell signals.

### Signals
- Buy Signal: A buy signal is triggered when there are at least two consecutive Renko blocks indicating an uptrend, combined with the MACD line crossing above the signal line. This is further confirmed if the slope of the MACD line is greater than the slope of the signal line, suggesting increasing momentum.
- Sell Signal: A sell signal is initiated when there are at least two consecutive Renko blocks in a downtrend with the MACD line crossing below the signal line. This signal is validated if the slope of the MACD line is less than the slope of the signal line, indicating decreasing momentum.

### Position Management
The strategy exits a position if the opposite signal is triggered or if the Renko blocks revert back to a neutral state. This method of position management helps in reducing potential losses from sudden market reversals.

## How It Works
- Data Downloading: The script fetches historical intraday data for selected stocks using the yfinance library.
- Renko Chart Calculation: Calculates Renko charts for each stock to determine significant price movements.
- MACD Calculation: Computes the MACD.
- Signal Processing: Analyzes the data from Renko charts and the MACD to produce buy and sell signals.
- Performance Evaluation: Evaluates the strategy's performance by calculating CAGR, Sharpe ratio, and maximum drawdown.

## Author
Muykheng Long - https://github.com/muykhenglong/
