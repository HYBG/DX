#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import MySQLdb
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()


if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-s', '--start', action='store', dest='start',default=None, help='start day')
    parser.add_option('-e', '--end', action='store', dest='end',default=None, help='end day')
    parser.add_option('-f', '--file', action='store', dest='file',default=None, help='off day')

 
    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    now = datetime.datetime.now()
    if ops.start and ops.end and ops.file:
        f = open(ops.file,'r')
        lines = f.readlines()
        f.close()
        offdays = []
        for row in lines:
            ymd = row.strip().split('-')
            offdays.append(datetime.date(int(ymd[0]),int(ymd[1]),int(ymd[2])))
        startymd = ops.start.split('-')
        endymd = ops.end.split('-')
        startday = datetime.date(int(startymd[0]),int(startymd[1]),int(startymd[2]))
        endday = datetime.date(int(endymd[0]),int(endymd[1]),int(endymd[2]))
        cday = startday
        ofn = '/var/data/iknow/tmp/calendar.csv'
        f = open(ofn,'w')
        while cday < endday:
            wd = cday.isoweekday()
            if not (wd==6 or wd==7 or (cday in offdays)):
                f.write('%04d-%02d-%02d\n'%(cday.year,cday.month,cday.day))
            cday = cday+datetime.timedelta(days=1)
        f.close()
        g_iu.importdata(ofn,'iknow_calendar')
    
    
    
    
    
    
    



