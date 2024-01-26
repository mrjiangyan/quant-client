#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from flask import jsonify

import traceback
import time

class ApiResult:
    def __init__(self, data, status=0, message='', success = True):
        self.result = data
        self.code = status
        self.success = success
        self.message = message
        self.timestamp = time.time()

    def to_json(self):
        return jsonify(self.__dict__)


def error_message(message):
    return ApiResult(None, -1, message).to_json()


def error():
    return ApiResult(None, -1, traceback.format_exc())
    # exc_type, exc_value, exc_traceback = sys.exc_info()
    # return ApiResult(None, -1, repr(traceback.format_exception(exc_type, exc_value,
    #                                       exc_traceback)))


def success(data=None, message=''):
    return ApiResult(data, status=0, message = message).to_json()
