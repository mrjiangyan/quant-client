#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from monitor.screener_sync import sync
from monitor.historical_sync import sync as history_sync
from datetime import datetime

def start_monitor():
    print('start_monitor')
    executors = {
        'default': ThreadPoolExecutor(10)
    }
    # 开启定时任务
    scheduler = BackgroundScheduler(executors=executors, timezone='Asia/Shanghai', daemon=True)
    
    scheduler.add_job(func= sync, id='sync', trigger="cron", 
        hour='6-16',  # 指定小时范围为 5 到 10
        minute='0',  # 分钟设为 0
        second='0',  # 秒设为 0
        max_instances=1,
        coalesce=False,
        misfire_grace_time=60)
    
    scheduler.add_job(func= history_sync, id='history_sync', trigger="cron",
                      max_instances=3,
                  hour='9-20', minute='*/15', misfire_grace_time = 25 * 60)
   
    scheduler.start()

