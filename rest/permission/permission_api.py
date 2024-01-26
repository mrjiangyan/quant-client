#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import json
import uuid

import flask


import logging
from auth.auth import login_required
# from data import database
# from data.model.business_engine import BusinessEngine
# from data.model.device import Device
# from data.model.device_monitoring_area import DeviceMonitoringArea
# from data.model.engine_device_area import EngineDeviceArea
# from data.model.sop_flow_process import SOPFlowProcess
# from data.request.business_engine.basic_model_area_update_form import BasicModelAreaUpdateForm
# from data.request.business_engine.business_engine_device_add_form import BusinessEngineDeviceAddForm
# from data.request.business_engine.sop_flow_device_area_update_form import SOPFlowDeviceAreaUpdateForm
# from data.request.business_engine.sop_flow_device_update_form import SOPFlowDeviceUpdateForm

# from monitor.camera_monitor import do_write_protocol_json
from rest.ApiResult import ApiResult, error_message
# from rest.device.device_api import is_exist_device
# from rest.device.monitoring_area_api import is_exist_monitoring_areas

blueprint = flask.Blueprint(
    'permission_api',
    __name__
)




# 获取业务引擎列表
@login_required
@blueprint.route('/api/permission/getPermCode', methods=['GET'])
def getPermCode(): 
    return ApiResult({
        "allAuth": [
            {
                "action": "btn:add",
                "describe": "btn:add",
                "type": "1",
                "status": "1"
            },
            {
                "action": "system:user:add",
                "describe": "新增用户",
                "type": "1",
                "status": "1"
            }
        ],
        "auth": [
            {
                "action": "system:user:add",
                "describe": "新增用户",
                "type": "1"
            }
        ],
        "codeList": [
            "system:user:add"
        ],
        "sysSafeMode": False
    }).to_json()
    
@login_required
@blueprint.route('/api/permission/getUserPermissionByToken', methods=['GET'])
def getUserPermissionByToken(): 
    return ApiResult({
        "allAuth": [
            {
                "action": "system:user:add",
                "describe": "新增用户",
                "type": "1",
                "status": "1"
            }
        ],
        "auth": [
            {
                "action": "system:user:add",
                "describe": "新增用户",
                "type": "1"
            }
        ],
        "menu": [
            {
                "redirect": None,
                "path": "/base/system/user",
                "component": "system/user/index",
                "route": "1",
                "meta": {
                    "keepAlive": False,
                    "internalOrExternal": False,
                    "icon": "ant-design:tag-twotone",
                    "componentName": "index",
                    "title": "用户管理"
                },
                "homepageFlag": 0,
                "name": "base-system-user",
                "id": "1642792505780813826",
                "isNavigation": False
            },
            {
                "redirect": None,
                "path": "/base/system/roles1",
                "component": "system/role/index",
                "route": "1",
                "meta": {
                    "keepAlive": False,
                    "internalOrExternal": False,
                    "icon": "ant-design:tag-twotone",
                    "componentName": "index",
                    "title": "角色管理"
                },
                "homepageFlag": 0,
                "name": "base-system-roles1",
                "id": "1641750607694983170",
                "isNavigation": False
            },
            {
                "redirect": False,
                "path": "/quant/symbol",
                "component": "quant/symbol/index",
                "route": "1",
                "meta": {
                    "keepAlive": False,
                    "internalOrExternal": False,
                    "icon": "ant-design:tag-twotone",
                    "componentName": "index",
                    "title": "Symbol管理"
                },
                "homepageFlag": 0,
                "name": "quant-symbol",
                "id": "1649950746074492929",
                "isNavigation": False
            },
            {
                "redirect": None,
                "path": "/quant/strategy",
                "component": "quant/strategy/index",
                "route": "1",
                "meta": {
                    "keepAlive": False,
                    "internalOrExternal": False,
                    "icon": "ant-design:tag-twotone",
                    "componentName": "index",
                    "title": "策略管理"
                },
                "homepageFlag": 0,
                "name": "quant-strategy",
                "id": "1649950945614311425",
                "isNavigation": False
            },
            {
                "redirect": False,
                "path": "/setting/dict",
                "component": "system/dict/index",
                "route": "1",
                "meta": {
                    "keepAlive": False,
                    "internalOrExternal": False,
                    "icon": "ant-design:audit-outlined",
                    "componentName": "index",
                    "title": "数据字典"
                },
                "homepageFlag": 0,
                "name": "setting-dict",
                "id": "1683358416035053570",
                "isNavigation": False
            },
            {
                "redirect": False,
                "path": "/setting/property",
                "component": "setting/frequency/index",
                "route": "1",
                "meta": {
                    "keepAlive": False,
                    "internalOrExternal": False,
                    "icon": "ant-design:tag-twotone",
                    "componentName": "index",
                    "title": "资产管理"
                },
                "homepageFlag": 0,
                "name": "setting-property",
                "id": "1649951160031326209",
                "isNavigation": False
            }
        ],
        "sysSafeMode": False
    }).to_json()

