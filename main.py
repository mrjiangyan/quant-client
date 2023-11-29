#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from flask import make_response, jsonify
from gevent import pywsgi
import traceback

import monitor

from flask import Flask
from flask_cors import CORS
from loguru import logger
import os
import faulthandler
from data import database

faulthandler.enable()

def create_app():
    app = Flask(__name__)

     # 必须要通过app上下文去启动数据库
    database.global_init("edge.db")
    # 添加api接口到
    register_api(app)

    app.config['JSON_AS_ASCII'] = False
    # app.after_request(auth.after_request)
    # app.before_request(auth.jwt_authentication)
  
    # app.config.from_object(config)

    # 注册日志
    config_logging()
    # 添加定时任务
    monitor.start_monitor()
    # add_task()
    # 解决跨域问题
    CORS(app)
    return app


def register_api(app):
    # 添加api接口到
    print('register_api')
    # app.register_blueprint(index.blueprint)
    # app.register_blueprint(system_api.blueprint)


def config_logging():
    os.chdir("./")  # 日志写入地址
    logger.add("./logs/log_{time}.log", rotation="1 day", retention="7 days")
    logger.add("./logs/error/log_{time}.log", rotation="1 day", level='ERROR',retention="7 days")


app = create_app()

@app.errorhandler(404)
def not_found(error):
    logger.error(error)
    return make_response(jsonify({'error': 'Not found'}), 404)


# 定义错误的处理方法
@app.errorhandler(Exception)
def error_handler(e):
    logger.error(traceback.format_exc())
    # return error_message(str(e))


if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 80), app)
    server.serve_forever()
