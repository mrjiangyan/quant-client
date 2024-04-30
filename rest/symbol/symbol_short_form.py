import wtforms
from .symbol_form import SymbolModifyForm

from wtforms.validators import DataRequired

class SymbolShortForm(SymbolModifyForm):
    short = wtforms.IntegerField()
     
    def validate(self):
        if not super().validate():
            return False

        if "short" not in self.data:
            self.short.errors.append("是否做空字段值不能为空")
            return False

        short_value = self.short.data
        if short_value not in [0, 1]:
            self.short.errors.append("short字段值必须为0或1")
            return False

        return True
