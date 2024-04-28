#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from monitor.historical_sync import sync as history_sync
from datetime import datetime

def start_monitor():
    print('start_monitor')
    executors = {
        'default': ThreadPoolExecutor(10)
    }
    # 开启定时任务
    scheduler = BackgroundScheduler(executors=executors, timezone='Asia/Shanghai', daemon=True)
    
    
    scheduler.add_job(func= history_sync, id='history_sync', trigger="cron",
                      max_instances=3,
                   minute='*/15', misfire_grace_time = 25 * 60)
   
    scheduler.start()

