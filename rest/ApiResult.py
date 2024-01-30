#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from flask import jsonify

import traceback
import time
import json

class ApiResult():
    def __init__(self, data:any=None, status:int=0, message:str='', success:bool = True):
        self.result = data
        self.code = status
        self.success = success
        self.message = message
        self.timestamp = time.time()
   
def error_message(message):
    result= ApiResult('', status = -1, message = message)
    # return jsonify(result)
    return json.dumps(result.__dict__)


def error():
    return ApiResult(status = -1, message = traceback.format_exc())
    # exc_type, exc_value, exc_traceback = sys.exc_info()
    # return ApiResult(None, -1, repr(traceback.format_exception(exc_type, exc_value,
    #                                       exc_traceback)))


def success(data=None, message=''):
    if hasattr(data, '__dict__'):
        result = ApiResult(data.__dict__, message= message)
    else:
        result = ApiResult(data,  message = message)
    return json.dumps(result.__dict__)

