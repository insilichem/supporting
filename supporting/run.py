#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
import logging, atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from supporting.web import app, clean_uploads


def schedule():
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=clean_uploads,
        trigger=IntervalTrigger(hours=6),
        id='clean_job',
        name='Clean upload files if older than interval',
        replace_existing=True)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

schedule()
logging.basicConfig()
