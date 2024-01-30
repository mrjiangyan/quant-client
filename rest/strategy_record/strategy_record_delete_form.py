import wtforms
from data.request.page_form import PageQueryForm
from data.request.JsonForm import JsonForm

class StrategyRecordDeleteForm(JsonForm):
    
    path = wtforms.StringField()


   
