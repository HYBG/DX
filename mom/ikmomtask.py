#!/usr/bin/python

import os
import sys
import urllib2
import logging
import string
import re
import datetime
import time
import math
import random
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikmomutil import ikmomutil

g_imu = ikmomutil()

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-n', '--name', action='store', dest='name',default=None, help='user name')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    if ops.name:
        pid = g_imu.pid(ops.name)
        next = g_imu.nextday()
        plan = g_imu.buildplan(pid,next)
        status = 0
        while 1:
            now = datetime.datetime.now()
            if next != '%04d-%02d-%02d'%(now.year,now.month,now.day):
                continue
            if 2 == g_imu.isduring(next):
                status = 1
                g_imu.exeplan(plan)
            elif 3 == g_imu.isduring(next):
                if now.hour=19 and status == 1:
                    next = g_imu.nextday()
                    plan = g_imu.buildplan(pid,next)
                    status = 0
            time.sleep(1)

                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
