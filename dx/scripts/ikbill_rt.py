#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import random
import socket
import urllib2
import commands
import random
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
import MySQLdb
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME')
if not g_home:
    raise Exception('IKNOW_HOME not found!')

sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('ikbill_rt')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'ikbill_rt.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class ikbill_rt:
    def __init__(self):
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()
    
    def __del__(self):
        self._cursor.close()
        self._conn.close()
        
    def _reconn(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()
    
    def _exesqlone(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchone()
        
    def _exesqlbatch(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchall()
        
    def _task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    g_logger.info('execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                g_logger.error('execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._conn.rollback()
                return False
        self._conn.commit()
        return True
        
    def _isopen(self):
        now = datetime.datetime.now()
        wd = now.isoweekday()
        o1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=9,minute=30,second=0)
        c1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=11,minute=30,second=0)
        o2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=13,minute=0,second=0)
        c2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=0,second=0)
        if wd == 6 or wd == 7:
            return False
        if now < o1 or now > c2 or (now>c1 and now < o2):
            return False
        url = 'http://hq.sinajs.cn/list=sz399001'
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            if info[-3] == '%04d-%02d-%02d'%(now.year,now.month,now.day):
                return True
        except Exception, e:
            g_logger.warning('get current url[%s] exception[%s]'%(url,e))
            return None

    def _rtprice(self,code):
        market = None
        if code[:2]=='60' or code[0]=='5':
            market = 'sh'
        else:
            market = 'sz'
        url = 'http://hq.sinajs.cn/list=%s%s'%(market,code)
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            v = (info[30],info[31],float(info[3]),float(info[6]),float(info[7]),float(info[8]),float(info[9]))
            return v
        except Exception, e:
            g_logger.warning('get current price code[%s] exception[%s]'%(code,e))
            return None

    def run(self):
        g_logger.info('ikbill_rt start....')
        while 1:
            codes = g_iu.allcodes()
            if self._isopen():
                sqls = []
                for code in codes:
                    inf = self._rtprice(code)
                    if inf:
                        sqls.append(('insert into ikbill_data_rt(code,date,time,currentp,buy1,sell1,volh,voly) values(%s,%s,%s,%s,%s,%s,%s,%s)',(code,)+inf))
                self._task(sqls)
            time.sleep(2)
        g_logger.info('ikbill_rt stop....')

if __name__ == "__main__":

    im = ikbill_rt()
    im.run()


