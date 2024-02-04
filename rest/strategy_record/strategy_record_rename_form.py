import wtforms
from wtforms.validators import DataRequired
from .strategy_record_delete_form import StrategyRecordDeleteForm

class StrategyRecordRenameForm(StrategyRecordDeleteForm):
    
    taskName = wtforms.StringField(validators=[DataRequired(message="新的任务名称不能为空"),])


   
