#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import urllib2
import socket
import MySQLdb
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

class hyzs:
    def __init__(self):
        self._url = 'http://hq.sinajs.cn/list=sh000001,sz399001,sz399006,sh000300,sh000905,sh000016'
        self._lastdl = None
        self._conn = None
        self._cursor = None
        logd = '/var/data/iknow/log'
        if not os.path.isdir(logd):
            os.makedirs(logd, 0777)
        self._logger = logging.getLogger('hyzs')
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logfile = os.path.join(logd,'hyzs.log')
        rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
        rh.setLevel(logging.INFO)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(logging.INFO)
    
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
            self._logger.error('hyzs connect db[%s] error[%s]'%(dbname,e))
        return False
        
    def reconn(self,dbname):
        try:
            self._cursor.close()
            self._conn.close()
            self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._conn.cursor()
            return True
        except Exception,e:
            self._logger.error('hyzs reconnect db[%s] error[%s]'%(dbname,e))
        return False
        
    def task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    self._logger.info('hyzs execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                self._logger.error('hyzs execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._conn.rollback()
                return False
        self._conn.commit()
        return True

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
    def rtprice(self):
        try:
            rows = urllib2.urlopen(self._url).readlines()
            mat = []
            for line in rows:
                sp = line.split('"')
                code = sp[0].split('_')[-1][2:8]
                info = sp[1].split(',')
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
                    v = (code,dt,'%0.4f'%op,'%0.4f'%hi,'%0.4f'%lo,'%0.4f'%cl,'%0.2f'%volh,'%0.4f'%volwy)
                    #print 'output[%s]'%str(v)
                    mat.append(v)
                else:
                    print ('update date[%04d-%02d-%02d] no data'%(now.year,now.month,now.day))
            return mat
        except Exception, e:
            print ('get current price exception[%s]'%(e))
            return None
            
    def run(self):
        lastd = None
        self.conn('hy')
        while 1:
            now = datetime.datetime.now()
            wd = now.isoweekday()
            if wd!=6 and wd!=7 and now.hour>=16 and lastd != '%04d-%02d-%02d'%(now.year,now.month,now.day):
                mat = self.rtprice()
                sqls = []
                for row in mat:
                    sqls.append(('insert into iknow_zhishu(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',row))
                if self.task(sqls,True):
                    lastd = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            time.sleep(360)

            
if __name__ == "__main__":

    hyzs().run()
    
    
    
    