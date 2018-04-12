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

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('dxindex')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'dxindex.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class dxindex:
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
        
    def run(self,start,end):
        conf = g_iu.loadcsv(os.path.join(os.path.join(g_home,'etc'),'code.csv'),{},0)
        codes = conf.keys()
        codes.sort()
        mat = []
        cnt = self._exesqlone('select count(*) from iknow_daily where date>%s and date<=%s',(start,end))
        cnt = cnt[0]
        for code in codes:
            print 'deal with code[%s]...'%code
            ccnt = self._exesqlone('select count(*) from iknow_data where code=%s and date>%s and date<=%s',(code,start,end))
            if (float(ccnt[0])>0.9*float(cnt)):
                vol = self._exesqlone('select avg(volwy) from iknow_data where code=%s and date>%s and date<=%s order by date',(code,start,end))
                inf = self._exesqlone('select name,boardname from iknow_name where code=%s',(code,))
                mat.append((code,inf[0],inf[1],vol[0]))
        mat.sort(reverse=True,key=lambda x:x[3])
        g_iu.dumpfile(os.path.join(g_home,'dxindex_%s_%s.csv'%(start,end)),mat)

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-s', '--start', action='store', dest='start',default=None, help='start day')
    parser.add_option('-e', '--end', action='store', dest='end',default=None, help='end day')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)
        
    if ops.start:
        end = datetime.date.today()
        end = '%04d-%02d-%02d'%(end.year,end.month,end.day)
        if ops.end:
            end = ops.end
        dxindex().run(ops.start,end)
        
        
        
        