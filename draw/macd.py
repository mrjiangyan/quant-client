import pandas as pd
import os
from datetime import datetime, timedelta
import pytz

short_window = 12
long_window = 26
signal_window = 9
    
# 计算MACD和DEA
def calculate_macd(data, short_window, long_window, signal_window):
    data['Close'] = pd.to_numeric(data['Close'])
    # 计算短期和长期指数移动平均
    short_ema = data['Close'].ewm(span=short_window, adjust=False).mean()
    long_ema = data['Close'].ewm(span=long_window, adjust=False).mean()

    # 计算DIF（差离值）
    dif = short_ema - long_ema

    # 计算MACD
    macd = dif.ewm(span=signal_window, adjust=False).mean()

    # 计算DEA
    dea = macd.ewm(span=signal_window, adjust=False).mean()

    # 计算信号线
    signal_line = macd.ewm(span=signal_window, adjust=False).mean()

    # 计算柱状图
    histogram = macd - signal_line

    return dif, macd, dea, signal_line, histogram

# 绘制股票价格和MACD图表
def plot_macd(data, dif, macd, dea, signal_line, histogram):
    import matplotlib.pyplot as plt

    plt.figure(figsize=(12, 8))

    # 绘制股票价格
    plt.subplot(2, 1, 1)
    plt.plot(data['Close'], label='Close Price', color='blue')
    plt.title('Stock Price and MACD')
    plt.legend()

    # 绘制MACD、DEA和信号线
    plt.subplot(2, 1, 2)
    plt.plot(dif, label='DIF', color='green')
    plt.plot(macd, label='MACD', color='red')
    plt.plot(dea, label='DEA', color='orange')  # 添加DEA曲线
    plt.plot(signal_line, label='Signal Line', color='blue')
    plt.bar(histogram.index, histogram, label='Histogram', color='gray')
    plt.legend()

    plt.show()
    
# 主函数
def main():
   
    file_path = os.path.join(os.getcwd(), 'resources', 'historical_data/1d/AAPL.csv')
    print(file_path)
    stock_data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')  
    stock_data.index = pd.to_datetime(stock_data.index, utc=True)
    end_date = datetime.now(pytz.utc)
    start_date = end_date - timedelta(days=3 * 365)
    stock_data = stock_data[(stock_data.index >= start_date) & (stock_data.index <= end_date)]

    # 计算MACD和DEA
    dif, macd, dea, signal_line, histogram = calculate_macd(stock_data, short_window, long_window, signal_window)

    # 绘制图表
    plot_macd(stock_data, dif, macd, dea, signal_line, histogram)

if __name__ == "__main__":
    main()
