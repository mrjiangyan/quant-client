from .login import login_api
from .strategy import strategy_api
from .user import user_api
from .symbol import symbol_api

from flask import Flask

def register_api(app:Flask):
    print('register_api')
    app.register_blueprint(strategy_api.blueprint)
    app.register_blueprint(login_api.blueprint)
    app.register_blueprint(user_api.blueprint)
    app.register_blueprint(symbol_api.blueprint)