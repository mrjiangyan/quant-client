import wtforms
from data.request.JsonForm import JsonForm

from wtforms.validators import DataRequired

class SymbolModifyForm(JsonForm):
    symbol = wtforms.StringField(validators=[DataRequired(message="symbol不能为空")])
    
    market =  wtforms.StringField(validators=[DataRequired(message="market不能为空")])
    
    cn_name = wtforms.StringField()
