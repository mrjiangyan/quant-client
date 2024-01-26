#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import json
import uuid

import flask

from auth.auth import login_required

from rest.ApiResult import ApiResult, error_message

blueprint = flask.Blueprint(
    'user_api',
    __name__
)




# 获取业务引擎列表
@login_required
@blueprint.route('/api/user', methods=['GET'])
def login(): 
    return ApiResult({
        "userId": "1",
        "username": "vben",
        "realName": "Vben Admin",
        "avatar": "",
        "desc": "manager",
        "password": "123456",
        "token": "fakeToken1",
        "homePath": "/dashboard/analysis",
        "roles": [
            {
                "roleName": "Super Admin",
                "value": "super"
            }
        ]
    }).to_json()

