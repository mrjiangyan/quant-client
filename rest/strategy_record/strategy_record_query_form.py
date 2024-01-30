import wtforms
from data.request.page_form import PageQueryForm

class StrategyRecordQueryForm(PageQueryForm):
    
    strategy_name = wtforms.StringField()
    
    # path = wtforms.StringField()

   
