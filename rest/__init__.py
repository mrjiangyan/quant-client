from .login import login_api
from .strategy import strategy_api
from .user import user_api
from .symbol import symbol_api
from .permission import permission_api
from .strategy_record import strategy_record_api
from .history import history_api
from .backtrader import backtrader_api
from .dict import dict_api
from .index import index

from flask import Flask

def register_api(app:Flask):
    print('register_api')
    app.register_blueprint(strategy_api.blueprint)
    app.register_blueprint(login_api.blueprint)
    app.register_blueprint(user_api.blueprint)
    app.register_blueprint(symbol_api.blueprint)
    app.register_blueprint(permission_api.blueprint)
    app.register_blueprint(strategy_record_api.blueprint)
    app.register_blueprint(history_api.blueprint)
    app.register_blueprint(backtrader_api.blueprint)
    app.register_blueprint(dict_api.blueprint)
    app.register_blueprint(index.blueprint)