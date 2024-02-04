#!/usr/bin/python3
# -*- coding: UTF-8 -*-


import flask
import importlib
import inspect
# 示例：假设策略类定义在名为 "strategies" 的模块中
module_name = "strategy"
strategy_set = set()

def get_all_classes(module_name):
    module = importlib.import_module(module_name)
    all_classes = [obj[1] for obj in inspect.getmembers(module, inspect.isclass) if issubclass(obj[1], object) and obj[1] is not object]
    return all_classes

all_strategies = get_all_classes(module_name)

strategy_objects = []
for index, strategy in enumerate(all_strategies):
    if strategy.__name__ == 'BaseStrategy':
        continue
    strategy_name = getattr(strategy.params, 'name')
    strategy_objects.append({ 'strategy_name':strategy_name, 'strategy': strategy.__name__ })

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
from rest.ApiResult import error_message, success
# from rest.device.device_api import is_exist_device
# from rest.device.monitoring_area_api import is_exist_monitoring_areas

blueprint = flask.Blueprint(
    'strategy_api',
    __name__
)


# 获取策略列表
@login_required
@blueprint.route('/api/strategy/list', methods=['GET'])
def list(): 
    page_result = {
        "current": 1,
        "total": len(strategy_objects),
        "size": len(strategy_objects),
        "pages": 1,
        "records": strategy_objects
    }
    return success(page_result)

