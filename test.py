from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime
import backtrader as bt
import os.path  # 路径模块
import sys  # 系统模块

class MyStrategy(bt.Strategy):
    params = (
        ("period_me1", 12),
        ("period_me2", 26),
        ("period_signal", 9)
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.period_me1,
            period_me2=self.params.period_me2,
            period_signal=self.params.period_signal
        )

    def next(self):
        date = self.data.datetime.date(0)
        dif = self.macd.lines.macd[0]
        dea = self.macd.lines.signal[0]
        print(f"日期: {date}, DIF: {dif:.4f}, DEA: {dea:.4f}")

         # If available, print additional attributes
        if hasattr(self.macd.lines, 'histo'):
            hist = self.macd.lines.histo[0]
            print(f"MACD Histogram: {hist:.4f}")


if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MyStrategy)

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, f'historical_data/1d/NIO.csv')
    # 加载你的数据
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(2014, 1, 1),
        todate=datetime.datetime(2023, 11, 28),
        reverse=False
    )

    cerebro.adddata(data)
    cerebro.run()
