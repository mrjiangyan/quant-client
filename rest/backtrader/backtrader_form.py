import wtforms

from data.request.JsonForm import JsonForm
from wtforms.validators import DataRequired, NumberRange

class BackTraderForm(JsonForm):
    strategy = wtforms.StringField(validators=[DataRequired(message="策略不能为空")])
    
    symbols = wtforms.StringField()

    period = wtforms.StringField(default ='1d', validators=[DataRequired(message="period不能为空")])
    
    days = wtforms.IntegerField(default =1, validators=[DataRequired(message="days能为空且不能小于5"), NumberRange(min=5, max=3000, message="days必须大于%(min)d且小于%(max)d")])

#g 根据已有的回测记录进行回测的地址
class BackTraderRetryForm(JsonForm):
    path = wtforms.StringField(validators=[DataRequired(message="回测记录目录不能为空")])
        
    
