from data.database_influxdb import MyInfluxDBClient
import pandas as pd
from datetime import datetime, timedelta
import pytz
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc

bucket_name= "stock-bucket-day"

measurement_prefix = "stock_k_line_"

influxdb_instance = MyInfluxDBClient()



window = 20
long_window = 26
signal_window = 9
linewidth = 0.5 


# 计算MACD和DEA
def calculate_bollinger(data):
    print(data)
    # 将时间转换为数字
    data['_time'] = pd.to_datetime(data['_time'])
    data['_time'] = mdates.date2num(data['_time'])

    data['close'] = pd.to_numeric(data['close']).round(2)
    data['open'] = pd.to_numeric(data['open'])
    data['high'] = pd.to_numeric(data['high'])
    data['low'] = pd.to_numeric(data['low'])
    # 假设你有一个包含日期和收盘价的 DataFrame，列名为 'Date' 和 'Close'
    # 这里的示例数据是从 Yahoo Finance 下载的苹果（AAPL）股票的每日收盘价
    # 你可以用你的实际数据替换这部分代码

    # 1. 计算中轨线（20日简单移动平均线）
    data['MA'] = data['close'].rolling(window=window).mean().round(3)

    # 2. 计算标准差（20日标准差）
    data['STD'] = data['close'].rolling(window=window).std().round(3)

    # 3. 计算上轨线和下轨线（假设标准差倍数为2）
    data['Upper_Band'] = (data['MA'] + 2 * data['STD']).round(3)
    data['Lower_Band'] = (data['MA'] - 2 * data['STD']).round(3)
    return data

# 绘制股票价格和MACD图表
def plot_bollinger(data):
    import matplotlib.pyplot as plt


    # 设置图表样式
    plt.style.use('dark_background')

    # 绘制收盘价、中轨线、上轨线和下轨线
    plt.figure(figsize=(12, 6))
    plt.plot(data['_time'], data['close'], label='Close Price', color='white', linewidth=linewidth)
    # 设置20-Day MA的颜色和线型
    plt.plot(data['_time'], data['MA'], label='20-Day MA', color='pink', linestyle='-', linewidth=linewidth)

    # 设置Upper Band的颜色和线型
    plt.plot(data['_time'], data['Upper_Band'], label='Upper Band', color='yellow', linestyle='-', linewidth=linewidth)

    # 设置Lower Band的颜色和线型
    plt.plot(data['_time'], data['Lower_Band'], label='Lower Band', color='lightblue', linestyle='-', linewidth=linewidth)
    
    
    # 添加网格线
    plt.grid(True, linestyle='--', alpha=0.5)

    # 绘制K线图
    fig, ax = plt.subplots(figsize=(12, 6))
    
    k_line_data = data[['_time', 'open', 'close', 'high', 'low']]

    # Convert time to numeric
    k_line_data['_time'] = mdates.date2num(k_line_data['_time'])

    # Plotting
    # fig, ax = plt.subplots(figsize=(12, 6))
    # Plotting candlestick chart
    candlestick_ohlc(ax, data[['_time', 'open', 'close', 'high', 'low']].values, width=0.6, colorup='r', colordown='g')

    # 设置x轴为日期
    ax.xaxis_date()
    
    # 获取最新的指标值
    latest_data = data.iloc[-1]
    latest_close = latest_data['close']
    latest_ma = latest_data['MA']
    latest_upper_band = latest_data['Upper_Band']
    latest_lower_band = latest_data['Lower_Band']

    # 在图表上显示最新的指标值
    plt.text(data['_time'].iloc[-1], latest_close, f"Close: {latest_close}", color='white')
    plt.text(data['_time'].iloc[-1], latest_ma, f"20-Day MA: {latest_ma}", color='pink')
    plt.text(data['_time'].iloc[-1], latest_upper_band, f"Upper:{latest_upper_band}", color='yellow')
    plt.text(data['_time'].iloc[-1], latest_lower_band, f"Lower:{latest_lower_band}", color='lightblue')

    # 添加标题和图例
    plt.title('Bollinger Bands')
    plt.legend()

    # 显示图形
    plt.show()
    
# 主函数
def main():
     # 获取当前日期
    current_date = datetime.now()

    # 计算2年前的日期
    two_years_ago = current_date - timedelta(days=600)
    start_date = two_years_ago.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date =  current_date.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    print(start_date, end_date)
    flux_query = f'''
    from(bucket: "{bucket_name}")
      |> range(start: {start_date}, stop: {end_date})
      |> filter(fn: (r) => r["_measurement"] == "{measurement_prefix}1d")
      |> filter(fn: (r) => r["stock_code"] == "aapl")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> keep(columns: ["_time", "close","open","high","low"])
      |> yield(name: "daily_close")
    '''

    # print(flux_query)
    # Execute the Flux query
    stock_data = influxdb_instance.query_data_frame(query=flux_query)
 
    # 计算MACD和DEA
    stock_data = calculate_bollinger(stock_data)

    # 绘制图表
    plot_bollinger(stock_data)

if __name__ == "__main__":
    main()
