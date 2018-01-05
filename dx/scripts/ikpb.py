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
import httplib
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()

class planb:
    def __init__(self,host,user,passwd,db,charset):
        self._host = host
        self._user = user
        self._passwd = passwd
        self._db = db
        self._charset = charset
        self._conn = MySQLdb.connect(host=self._host,user=self._user,passwd=self._passwd,db=self._db,charset=self._charset)
        self._cursor = self._conn.cursor()

    def __del__(self):
        self._cursor.close()
        self._conn.close()
        
    def set(self,host,user,passwd,db,charset):
        self._host = host
        self._user = user
        self._passwd = passwd
        self._db = db
        self._charset = charset

    def reconn(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host=self._host,user=self._user,passwd=self._passwd,db=self._db,charset=self._charset)
        self._cursor = self._conn.cursor()

    def exesqlone(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchone()
        
    def exesqlbatch(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchall()
        
    def task(self,sqls,log=False):
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
        
if __name__ == "__main__":
    try:
        conf = os.path.join(os.path.join(g_home,'etc'),'code_dl.csv')
        lastd = g_iu.loadcsv(conf,{},0)
        codes = lastd.keys()
        codes.sort()
        pb = planb('localhost','root','123456','hy','utf8')
        mat = []
        print 'ikplanb start...'
        for code in codes:
            try:
                start = '2018-01-01'
                if lastd.has_key(code):
                    start = lastd[code]
                print 'fetch code[%s] from date[%s]...'%(code,start)
                rows = pb.exesqlbatch('select code,date,open,high,low,close,zde,zdf,volh,volwy,zf,hs from iknow_data_ex where code=%s and date>%s',(code,start))
                for row in rows:
                    mat.append(row)
            except Exception,e:
                print 'code[%s] export exception[%s]....'%(code,e)
                continue
        ofn = os.path.join(os.path.join(g_home,'tmp'),'planb.csv')
        g_iu.dumpfile(ofn,mat)
        g_iu.importdata(ofn,'iknow_data')
        pb.reconn()
        mat = []
        for code in codes:
            ld = pb.exesqlone('select date from iknow_data where code=%s order by date desc limit 1',(code,))
            if len(ld)>0:
                mat.append((code,ld[0]))
        g_iu.dumpfile(conf,mat)
        pb.task([('update iknow_conf set value=%s where name=%s',('start','station'))])
    except Exception,e:
        g_iu.log(logging.INFO,'dlone exception[%s]....'%e)







