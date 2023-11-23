#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import threading
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from monitor.quote_sync import sync


def start_monitor():
    print('start_monitor')
    executors = {
        'default': ThreadPoolExecutor(10)
    }
    # 开启定时任务
    scheduler = BackgroundScheduler(executors=executors, timezone='Asia/Shanghai', daemon=True)

    # spy_4khdr_cn_thread = threading.Thread(target= spy, daemon=True)
    # spy_4khdr_cn_thread.start()
    
    # scheduler.add_job(func= spy, id='start_spy', trigger="interval", 
    #            minutes=60*6)
    
    scheduler.add_job(func= sync, id='sync', trigger="cron",  hour='*', minute='*', second='0', max_instances=1, coalesce=False)
   
    scheduler.start()
    
    # job_thread = threading.Thread(target=start_job_monitor, daemon=True)
    # job_thread.start()
    # camera_exception_thread = threading.Thread(target=start_camera_exception, daemon=True)
    # camera_exception_thread.start()

    # create_day_folder(datetime.datetime.now().strftime('%Y%m%d'))
