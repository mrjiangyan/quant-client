import wtforms
from wtforms.validators import DataRequired, NumberRange
from flask_wtf import FlaskForm

class PageQueryForm(FlaskForm):
    pageNo = wtforms.IntegerField(default =1, validators=[DataRequired(message="pageIndex能为空且不能小于1"),
                                                 NumberRange(min=1, message="pageIndex必须大于%(min)d且小于%(max)d")])
    pageSize = wtforms.IntegerField(default=10, validators=[DataRequired(message="pageSize不能为空且不能小于1"),
                                                NumberRange(min=1, max=1000, message="pageSize必须大于%(min)且小于%(max)")])
    order = wtforms.StringField(default='desc')
    
    column = wtforms.StringField()
    