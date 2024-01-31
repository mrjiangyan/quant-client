import wtforms
from data.request.page_form import PageQueryForm

class SymbolQueryForm(PageQueryForm):
    symbol = wtforms.StringField()

    keyword = wtforms.StringField()

    market = wtforms.StringField()
    
    country = wtforms.StringField()
    
    compute = wtforms.BooleanField()
   
