
  

class StrategyRecordSymbolDetail():
    
    def __init__(self, symbol:str, path: str, revenue: float = 0, detail:str=None):
        self.symbol = symbol
        self.path = path
        self.revenue = revenue
        self.detail = detail

