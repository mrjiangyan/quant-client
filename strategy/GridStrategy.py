from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy

class GridStrategy(BaseStrategy):
    params = (
        ("grid_size", 10),  # Grid size in points
        ("take_profit", 50),  # Take profit in points
        ("stop_loss", 50),  # Stop loss in points
    )

    def __init__(self):
        self.grid_size = self.params.grid_size
        self.take_profit = self.params.take_profit
        self.stop_loss = self.params.stop_loss

        self.buy_price_levels = []
        self.sell_price_levels = []

    def next(self):
        current_price = self.data.close[0]
        if not self.buy_price_levels:
            self.buy_price_levels.append(current_price - self.grid_size)

        if not self.buy_price_levels:
            self.buy_price_levels.append(current_price - self.grid_size)


        # Check for existing orders
        if self.buy_price_levels and current_price >= self.buy_price_levels[-1] + self.grid_size:
            # Place a buy order at the next lower grid level
            buy_price = self.buy_price_levels[-1] + self.grid_size
            cash_to_spend = self.broker.getvalue() * self.params.percent_of_cash
            size = cash_to_spend / self.data.close[0]
            self.buy_price_levels.append(buy_price)
            self.buy(size=size, price=buy_price)

        if self.sell_price_levels and current_price <= self.sell_price_levels[-1] - self.grid_size:
            # Place a sell order at the next higher grid level
            sell_price = self.sell_price_levels[-1] - self.grid_size
            self.sell_price_levels.append(sell_price)
            self.sell(data=self.data, price=sell_price, exectype=bt.Order.Limit)

        # Check for take profit and stop loss
        open_positions = self.getpositions()

        for position in open_positions:
            position_price = position.Close
          
            # Check for take profit
            if current_price >= position_price + self.take_profit:
                self.close(position)

            # Check for stop loss
            elif current_price <= position_price - self.stop_loss:
                self.close(position)
    
    
