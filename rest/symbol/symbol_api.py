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
    'symbol_api',
    __name__
)




# 获取业务引擎列表
# @login_required
@blueprint.route('/api/symbol/list', methods=['GET'])
def business_engine_list(): 
    return ApiResult([]).to_json()

