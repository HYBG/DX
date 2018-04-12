#!/usr/bin/python

import os
import sys
import string
import datetime
import urllib2
import MySQLdb
import time
import logging
from logging.handlers import RotatingFileHandler

logd = os.path.join('/tmp', 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('hsdl')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'hsdl.log')
rh = RotatingFileHandler(logfile, maxBytes=10*1024*1024,backupCount=10)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)


class hsdl:
    def __init__(self):
        self._conn = None
        self._cursor = None
        self.conn('hs')
        
    def __del__(self):
        if not self._cursor:
            self._cursor.close()
        if not self._conn:
            self._conn.close()
        
    def conn(self,dbname):
        try:
            self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._conn.cursor()
            return True
        except Exception,e:
            self.log(logging.ERROR,'iktool connect db[%s] error[%s]'%(dbname,e))
        return False
        
    def reconn(self,dbname):
        try:
            self._cursor.close()
            self._conn.close()
            self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._conn.cursor()
            return True
        except Exception,e:
            g_logger.error('iktool reconnect db[%s] error[%s]'%(dbname,e))
        return False

    def exesqlone(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        ret = ()
        if n==1:
            ret = self._cursor.fetchone()
        return ret

    def exesqlbatch(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        n = self._cursor.execute(sql,param)
        ret = ()
        if n>0:
            ret = self._cursor.fetchall()
        return ret
        
    def task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    g_logger.info('hsdl execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                g_logger.error('hsdl execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._conn.rollback()
                return False
        self._conn.commit()
        return True
    
    def _codes(self):
        data = self.exesqlbatch('select code from hs.hs_name order by code',None)
        codes = []
        for row in data:
            codes.append(row[0])
        return codes

    '''**************
    return value
    0:stock name
    1:today open
    2:yestoday close
    3:lastest price
    4:today high
    5:today low
    6:buy1
    7:sell1
    8:vol gu
    9:vol yuan
    10:buy1 volume 11:buy1 price
    12:buy2 volume 13:buy2 price
    14:buy3 volume 15:buy3 price
    16:buy4 volume 17:buy4 price
    18:buy5 volmue 19:buy5 price
    20:sell1 volume 21:sell1 price
    (22, 23),(24, 25),(26,27),(28, 29)sell2-5 volume and price
    30: 2008-01-11 date
    31: 15:05:32  time
    **************'''
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
            v = None
            now = datetime.datetime.now()
            if (float(info[9])>0) and (info[30] == '%04d-%02d-%02d'%(now.year,now.month,now.day)):
                dt = info[30]
                op = float(info[1])
                hi = float(info[4])
                lo = float(info[5])
                cl = float(info[3])
                volh = float(info[8])/100
                volwy = float(info[9])/10000
                v = (code,dt,op,hi,lo,cl,'%0.2f'%volh,'%0.4f'%volwy)
            else:
                g_logger.info('update code[%s] no data from URL[%s]'%(code,url))
            return v
        except Exception, e:
            g_logger.error('get current price code[%s] exception[%s]'%(code,e))
            return None

    def run(self):
        lastd = None
        while 1:
            mat = []
            codes = self._codes()
            now = datetime.datetime.now()
            wd = now.isoweekday()
            if wd!=6 and wd!=7 and now.hour>=16 and lastd != '%04d-%02d-%02d'%(now.year,now.month,now.day):
                codes = self._codes()
                sqls = []
                for code in codes:
                    v = self._rtprice(code)
                    if v:
                        sqls.append(('insert into hs.hs_daily_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',v))
                self.task(sqls)
                lastd = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            time.sleep(360)
            
    def firsttime(self):
        info = self.exesqlbatch('select code,name from dx.iknow_name',None)
        sqls = []
        for i in range(len(info)):
            line = info[i]
            sqls.append(('insert into hs.hs_name(code,name) values(%s,%s)',(line[0],line[1])))
        self.task(sqls,True)

if __name__ == "__main__":

    #hsdl().firsttime()
    hsdl().run()
    
    
    
    