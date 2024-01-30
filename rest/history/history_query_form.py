import wtforms
from flask_wtf import FlaskForm

class HistoryQueryForm(FlaskForm):
    symbol = wtforms.StringField()

    period = wtforms.StringField()

    
