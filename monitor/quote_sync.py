from pandas import DataFrame
from data.database_influxdb import MyInfluxDBClient
from influxdb_client import Point
from datetime import datetime, timedelta
from loguru import logger
import pytz
import yfinance as yf
import requests
import pandas as pd



bucket_name= "stock-bucket-day"

measurement_prefix = "stock_k_line_"

influxdb_instance = MyInfluxDBClient()
    
api_key="F4RM9RB7HHTFYPYO" 
    
def get_historical_data(symbol, period, interval) -> DataFrame:
    
    # 计算前一天的日期
    end_date = datetime.now() - timedelta(days=1)

    # 计算前60天的日期
    start_date = datetime.now() - timedelta(days=interval)

    stock_data = yf.download(symbol, start= start_date.strftime('%Y-%m-%d'), end= end_date.strftime('%Y-%m-%d'), interval=period)
    # historical_data = ticker.history(period=period, interval=interval)
    return stock_data

def get_historical_data_from_alphavantage(symbol) -> DataFrame:
    
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize=full&symbol={symbol}&apikey={api_key}'
    response = requests.get(url)
    stock_data = response.json()
    # 提取时间序列数据
    time_series_data = stock_data.get('Time Series (Daily)')
    if time_series_data == None:
        return None
    # 将数据转换为 DataFrame
    historical_data = pd.DataFrame(time_series_data).T

    # 将日期列转换为 datetime 类型
    historical_data.index = pd.to_datetime(historical_data.index)

    # 将数值列转换为浮点数
    historical_data[['1. open', '2. high', '3. low', '4. close', '5. volume']] = historical_data[['1. open', '2. high', '3. low', '4. close', '5. volume']].astype(float)

    # 重命名列
    historical_data.rename(columns={'1. open': 'Open', '2. high': 'High', '3. low': 'Low', '4. close': 'Close', '5. volume': 'Volume'}, inplace=True)

    # 打印 DataFrame
    logger.info(historical_data)
    return historical_data


def save_kline_data(symbol:str, market:str, historical_data:DataFrame, interval:str):
    influxdb_instance = MyInfluxDBClient()
    logger.info(f'{symbol}, {interval}')
    logger.info(f'{historical_data}')

    
    # 遍历每一行并获取每个字段的值
    for index, row in historical_data.iterrows():
        date = index
        #logger.info(date)
        # 尝试将其转换为日期时间类型
        # 检查是否为日期
        # if not pd.isna(pd.to_datetime(date, errors='coerce')):
        #     logger.info(row['index'])
        #     date = row['index']
        open_price = row['Open']
        high_price = row['High']
        low_price = row['Low']
        close_price = row['Close']
        volume = row['Volume']


        if interval == '1d':
            local_datetime = datetime.combine(date, datetime.min.time())
             # Convert the local datetime to UTC
            utc_timestamp = local_datetime.astimezone(pytz.utc)
        else:
            utc_timestamp = local_datetime = date
        # 打印每个字段的值
        # print(f"Date: {date},utc_timestamp:{utc_timestamp}, Open: {open_price}, High: {high_price}, Low: {low_price}, Close: {close_price}, Volume: {volume}")
        tags = {"market": market, "stock_code": symbol}
        measurement_name  = measurement_prefix + interval
        try:
            if influxdb_instance.check_data_existence(bucket_name, measurement_name, tags, utc_timestamp, utc_timestamp + timedelta(minutes=1)) == False:
                _point1 = (
                    Point(measurement_name)
                    .tag("stock_code", symbol)
                    .tag("market", market)
                    .time(utc_timestamp)
                    .field("open", open_price)
                    .field("high", high_price)
                    .field("low", low_price)
                    .field("close", close_price)
                    .field("volume", int(volume))
                    )
                influxdb_instance.write_data(bucket_name, data_points=[_point1])
            # else:
            #     logger.info(f'{measurement_name},{symbol},{utc_timestamp},{interval}数据已经存在')
        except Exception as err:
            print(err)
            print(f"Date: {date},utc_timestamp:{utc_timestamp}, Open: {open_price}, High: {high_price}, Low: {low_price}, Close: {close_price}, Volume: {volume}")
          


def sync():
    interval_map = {"1d": 600, '1m': 7, '5m': 59, '15m': 59, '30m': 59, "60m": 600, }
    # interval_map = {"1d": 600 }
    stock_symbol = ['aapl','nio', 'tsm','msft','li','xpev']
    # stock_symbol = ['aapl']
    market = 'US'
    
    # 获取当前日期
    current_date = datetime.now()

    # 计算2年前的日期
    two_years_ago = current_date - timedelta(days=600)
    utc_timestamp = two_years_ago.astimezone(pytz.utc)
    for symbol in stock_symbol:
        for key, value in interval_map.items():
            #循环查询最近1年的日线，
            kline_data = get_historical_data(symbol, period= key, interval=value)
            # 打印K线数据
            save_kline_data(symbol,'US', kline_data, key)
            
            measurement_name  = measurement_prefix + key
            tags = {"market": market, "stock_code": symbol}
            if key == "1d" and influxdb_instance.check_data_existence(bucket_name, measurement_name, tags, utc_timestamp, utc_timestamp + timedelta(minutes=1)) == False:
                # 循环所有历史数据
                kline_data = get_historical_data_from_alphavantage(symbol)
                if kline_data is not None:
                    save_kline_data(symbol,market , kline_data, key)
   
   
   
   
   
# print(ticker.summary_detail)

# # 获取财务指标数据
# financials_data = ticker.financial_data

# print(financials_data)
# # 获取公司信息
# company_info = ticker.summary_profile

# print(company_info)
# # 获取持有者信息
# holders_info = ticker.major_holders
# print(holders_info)
# # 获取分析师评级
# analyst_ratings = ticker.recommendations
# print(analyst_ratings)
# # 获取股票选项数据
# options_data = ticker.option_chain
# print(options_data)

