# 导入所需模块
from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime  # 日期时间模块
import os.path  # 路径模块
import sys  # 系统模块

# 导入backtrader平台
import backtrader as bt

class MyYahooFinanceCSVData(bt.feeds.YahooFinanceCSVData):
    # lines = ('Date', 'adjclose','Open', 'High', 'Low', 'Close', 'Volume')
    def start(self):
        # Rename 'Date' column to 'date'
        # self('Date', 'date')
        super(MyYahooFinanceCSVData, self).start()
        
# 创建策略
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' 日志函数 '''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 保留对数据序列中`close`线的引用
        self.dataclose = self.datas[0].close

    def next(self):
        date = self.datas[0].datetime.date(0)
        open_price = self.datas[0].open[0]
        high_price = self.datas[0].high[0]
        low_price = self.datas[0].low[0]
        close_price = self.datas[0].close[0]
        volume = self.datas[0].volume[0]

        # 输出每一行的记录
        self.log('日期: %s, 开盘价: %.2f, 最高价: %.2f, 最低价: %.2f, 收盘价: %.2f, 交易量: %.2f' %
                 (date.isoformat(), open_price, high_price, low_price, close_price, volume))
        # 记录数据序列的收盘价
        # self.log('收盘价, %.2f' % self.dataclose[0])

if __name__ == '__main__':
    # 创建cerebro实体
    cerebro = bt.Cerebro()
    # 添加策略
    cerebro.addstrategy(TestStrategy)

    # 数据在样本的子文件夹中。需要找到脚本所在的位置
    # 因为它可以从任何地方调用
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, 'historical_data/1d/A.csv')

    # 创建数据源
    data = bt.feeds.YahooFinanceCSVData(
        
        dataname=datapath,
        # 不传递此日期之前的值
        fromdate=datetime.datetime(1999,11,17),
        # 不传递此日期之后的值
        todate=datetime.datetime(1999, 11, 19),
        reverse=False,
        adjclose = False,
        dtformat='%Y-%m-%d %H:%M:%S%z',  # Adjust the date format according to your data
        adjvolume = False,
        # round = False,
        swapcloses = False,
        # roundvolume= 10,
        )

    
    for row in enumerate(data):
        print(row.datetime, row.open, row.high, row.low, row.close, row.volume)
    
    # 将数据源添加到Cerebro
    cerebro.adddata(data)

    # 设置我们所需的现金起始值
    cerebro.broker.setcash(100000.0)

    # 打印出起始条件
    print('起始投资组合价值：%.2f' % cerebro.broker.getvalue())

    # 运行所有
    cerebro.run()

    # 打印出最终结果
    print('最终投资组合价值：%.2f' % cerebro.broker.getvalue())
