from data.database import MyInfluxDBClient
import pandas as pd
from datetime import datetime, timedelta
import pytz
import pandas as pd

bucket_name= "stock-bucket-day"

measurement_prefix = "stock_k_line_"

influxdb_instance = MyInfluxDBClient()




window = 20
long_window = 26
signal_window = 9
    
# 计算MACD和DEA
def calculate_bollinger(data):
    print(data)
    data['close'] = pd.to_numeric(data['close'])
   # 假设你有一个包含日期和收盘价的 DataFrame，列名为 'Date' 和 'Close'
    # 这里的示例数据是从 Yahoo Finance 下载的苹果（AAPL）股票的每日收盘价
    # 你可以用你的实际数据替换这部分代码

    # 1. 计算中轨线（20日简单移动平均线）
    data['MA'] = data['close'].rolling(window=window).mean()

    # 2. 计算标准差（20日标准差）
    data['STD'] = data['close'].rolling(window=window).std()

    # 3. 计算上轨线和下轨线（假设标准差倍数为2）
    data['Upper_Band'] = data['MA'] + 2 * data['STD']
    data['Lower_Band'] = data['MA'] - 2 * data['STD']
    return data

# 绘制股票价格和MACD图表
def plot_bollinger(data):
    import matplotlib.pyplot as plt

    # 绘制收盘价、中轨线、上轨线和下轨线
    plt.figure(figsize=(12, 6))
    plt.plot(data['_time'], data['close'], label='Close Price', color='black')
    plt.plot(data['_time'], data['MA'], label='20-Day MA', color='blue')
    plt.plot(data['_time'], data['Upper_Band'], label='Upper Band', color='red', linestyle='--')
    plt.plot(data['_time'], data['Lower_Band'], label='Lower Band', color='green', linestyle='--')

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
      |> keep(columns: ["_time", "close"])
      |> yield(name: "daily_close")
    '''

    # print(flux_query)
    # Execute the Flux query
    stock_data = influxdb_instance.query_data_frame(query=flux_query)
    # 下载股票数据
    # stock_data = download_stock_data(ticker, start_date, end_date)

    # 计算MACD和DEA
    stock_data = calculate_bollinger(stock_data)

    # 绘制图表
    plot_bollinger(stock_data)

if __name__ == "__main__":
    main()
