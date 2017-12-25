#!/usr/bin/python

import os
import sys
import logging
import urllib2
import string
import re
import datetime
import time
import math
import MySQLdb
import signal
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()

def update():
    now = datetime.datetime.now()
    g_iu.log(logging.INFO,'import ikbill_data_ex date[%04d-%02d-%02d] start'%(now.year,now.month,now.day))
    codes = g_iu.allcodes()
    codes.sort()
    ofn = os.path.join(os.path.join(g_home,'tmp'),'dailyup_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
    f = open(ofn,'w')
    for code in codes:
        inf = rtprice(code)
        if inf:
            date = inf[30]
            op = float(inf[1])
            high = float(inf[4])
            low = float(inf[5])
            close = float(inf[3])
            last = float(inf[2])
            zde = close-last
            zdf = ((close-last)/last)*100
            volh = float(inf[8])/100.0
            volwy = float(inf[8])/10000.0
            zf = 100*(((high-last)/last)-((low-last)/last))
            line = '%s,%s,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f'%(code,date,op,high,low,close,zde,zdf,volh,volwy,zf)
            g_iu.log(logging.INFO,'line[%s]'%line)
            f.write('%s\n'%line)
    f.close()
    g_iu.importdata(ofn,'ikbill_data_ex')
    g_iu.log(logging.INFO,'import ikbill_data_ex date[%04d-%02d-%02d] done'%(now.year,now.month,now.day))

def rtprice(code):
    market = None
    if code[:2]=='60' or code[0]=='5':
        market = 'sh'
    else:
        market = 'sz'
    url = 'http://hq.sinajs.cn/list=%s%s'%(market,code)
    try:
        line = urllib2.urlopen(url).readline()
        info = line.split('"')[1].split(',')
        v = None
        now = datetime.datetime.now()
        if int(info[8])>0 and info[30]=='%04d-%02d-%02d'%(now.year,now.month,now.day):
            v = info
        return v
    except Exception, e:
        g_iu.log(logging.WARNING,'get current price code[%s] exception[%s]'%(code,e))
        return None

if __name__ == "__main__":
    lastday = None
    while 1:
        now = datetime.datetime.now()
        wd = now.isoweekday()
        if wd!=6 and wd!=7 and now.hour>=15 and now.minute>1:
            if lastday != '%04d-%02d-%02d'%(now.year,now.month,now.day):
                url = 'http://hq.sinajs.cn/list=sz399001'
                try:
                    line = urllib2.urlopen(url).readline()
                    info = line.split('"')[1].split(',')
                    if int(info[8])>0 and info[30] == '%04d-%02d-%02d'%(now.year,now.month,now.day):
                        update()
                        lastday = '%04d-%02d-%02d'%(now.year,now.month,now.day)
                except Exception, e:
                    g_iu.log(logging.WARNING,'get current url[%s] exception[%s]'%(url,e))
        time.sleep(5)







