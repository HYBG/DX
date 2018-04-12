#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import socket
import MySQLdb
import signal
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()

class iksync:
    def __init__(self):
        self._conf = g_iu.loadcsv(os.path.join(os.path.join(g_home,'etc'),'code_dl.csv'),{},0)
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()
    
    def __del__(self):
        self._cursor.close()
        self._conn.close()

    def _codes(self):
        codes = self._conf.keys()
        codes.sort()
        return codes

    def _reconn(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()

    def _exesqlone(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        ret = ()
        if n==1:
            ret = self._cursor.fetchone()
        return ret

    def _exesqlbatch(self,sql,param):
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
        
    def _task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    g_logger.info('ikdaily execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                g_logger.error('ikdaily execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._conn.rollback()
                return False
        self._conn.commit()
        return True
        
    def sync(self):
        codes = self._codes()
        mat = []
        for code in codes:
            ld = self._exesqlone('select date from iknow_data where code=%s order by date desc limit 1',(code,))
            mat.append((code,ld[0]))
        ofn = os.path.join(os.path.join(g_home,'etc'),'code_dl_nw.csv')
        cur = os.path.join(os.path.join(g_home,'etc'),'code_dl.csv')
        old = os.path.join(os.path.join(g_home,'etc'),'code_dl_old.csv')
        g_iu.dumpfile(ofn,mat)
        g_iu.execmd('mv %s %s'%(cur,old))
        g_iu.execmd('mv %s %s'%(ofn,cur))
        g_iu.execmd('rm -fr %s'%(ofn))


if __name__ == "__main__":
    iksync().sync()
        
        
        