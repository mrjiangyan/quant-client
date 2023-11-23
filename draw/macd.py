from data.database import MyInfluxDBClient
import pandas as pd

bucket_name= "stock-bucket-day"

measurement_prefix = "stock_k_line_"

influxdb_instance = MyInfluxDBClient()


short_window = 12
long_window = 26
signal_window = 9
    
# 计算MACD和DEA
def calculate_macd(data, short_window, long_window, signal_window):
    data['close'] = pd.to_numeric(data['close'])
    # 计算短期和长期指数移动平均
    short_ema = data['close'].ewm(span=short_window, adjust=False).mean()
    long_ema = data['close'].ewm(span=long_window, adjust=False).mean()

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
    plt.plot(data['close'], label='Close Price', color='blue')
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
    start_date = '2022-01-01T00:00:00Z'
    end_date = '2023-12-01T00:00:00Z'


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
    dif, macd, dea, signal_line, histogram = calculate_macd(stock_data, short_window, long_window, signal_window)

    # 绘制图表
    plot_macd(stock_data, dif, macd, dea, signal_line, histogram)

if __name__ == "__main__":
    main()
