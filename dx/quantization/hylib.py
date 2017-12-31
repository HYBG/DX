#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import commands
import random
from datetime import timedelta
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
import MySQLdb
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('hy')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'hy.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class hylib:
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

    #which day to tell
    def lasttell(self):
        ld = self._exesqlone('select date from iknow_tell order by date desc limit 1',None)
        next = self._exesqlone('select date from iknow_calendar where date>%s order by date limit 1',(ld[0],))
        return (ld[0],next[0])

    def tellbuy(self,offset=0):
        td = self._exesqlbatch('select date from iknow_tell order by date desc limit %d'%(offset+1),None)
        td = td[-1][0]
        buys = self._exesqlbatch('select code,ranking,volyy from iknow_after where date=%s and code in (select code from iknow_ops where date=%s and ops=1) order by ranking desc',(td,td))
        return list(buys)

    def tellsell(self,offset=0):
        td = self._exesqlbatch('select date from iknow_tell order by date desc limit %d'%(offset+1),None)
        td = td[-1][0]
        sells = self._exesqlbatch('select code,ranking,volyy from iknow_after where date=%s and code in (select code from iknow_ops where date=%s and ops=2) order by ranking desc',(td,td))
        return list(sells)

    def lastdata(self,code):
        ld = self._exesqlone('select date from iknow_tell order by date desc limit 1',None)
        base = self._exesqlone('select close,zdf,zf,hs,high,low from iknow_data where code=%s and date=%s',(code,ld[0]))
        aft = self._exesqlone('select score,ranking,volyy,crn,hrn,lrn from iknow_after where code=%s and date=%s',(code,ld[0]))
        rng = self._exesqlone('select ops,hrn,lrn,crn,ev,std from iknow_ops where code=%s and date=%s',(code,ld[0]))
        ps = self._exesqlone('select c1_ev,c1_std,h1_ev,h1_std,l1_ev,l1_std from iknow_tell where code=%s and date=%s',(code,ld[0]))
        data = [(base[0],base[1],base[2],base[3],base[4],base[5]),(aft[0],aft[1],aft[2],aft[3],aft[4],aft[5]),(rng[0],rng[1],rng[2],rng[3],rng[4],rng[5]),(ps[0],ps[1],ps[2],ps[3],ps[4],ps[5])]
        return data
        
    def process(self):
        station = self._exesqlone('select value from iknow_conf where name=%s',('station',))
        return station[0]
        
        
        
        
        
        