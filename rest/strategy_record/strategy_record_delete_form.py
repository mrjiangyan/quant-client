import wtforms
from data.request.JsonForm import JsonForm

class StrategyRecordDeleteForm(JsonForm):
    
    path = wtforms.StringField()


   
