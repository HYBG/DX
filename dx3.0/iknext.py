#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import Queue
import MySQLdb
import urllib2
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

sys.path.append(os.path.join(os.getenv('IKNOW_HOME','/var/data/iknow'),'lib'))
from ikdata import ikdata

class iknext(ikdata):
    def __init__(self,logfile=None,logon=False):
        home = os.getenv('IKNOW_HOME','/var/data/iknow')
        if logfile:
            ikdata.__init__(self,logfile,logon)
        else:
            ikdata.__init__(self,os.path.join(os.path.join(home,'log'),'iknext.log'),logon)
        self._defaultstart = '1987-05-07'

    def __del__(self):
        pass

    def reconn(self,dbname):
        try:
            self._cursor.close()
            self._connection.close()
            self._connection = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self.info('ikdata reconnect db[%s] error[%s]'%(dbname,e))
        return False

    def exesqlquery(self,sql,param,log=None):
        n = 0
        if log:
            self.info('ikdata prepare to query sql[%s],para[%s]'%(sql,str(param)))
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        mat = []
        while n>0:
            ret = self._cursor.fetchone()
            if len(ret)==1:
                mat.append(ret[0])
            elif len(ret)>1:
                mat.append(list(ret))
            n = n-1
        if log:
            self.info('ikdata query results[%d]'%(len(mat)))
        return mat

    def task(self,sqls,log=None):
        show = self._logon
        if log:
            show = log
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if show:
                    self.info('ikdata execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                self.error('ikdata execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._connection.rollback()
                return False
        self._connection.commit()
        return True

    def lastday(self,table,code=None,default=None):
        ld = None
        if code:
            ld = self.exesqlquery('select date from '+table+' where code=%s order by date desc limit 1',(code,))
        else:
            ld = self.exesqlquery('select date from '+table+' order by date desc limit 1',None)
        if ld and len(ld)>0:
            return ld[0]
        return default

    def lastdays(self,table,codes,default=None):
        dic = {}
        for code in codes:
            dic[code]=self.lastday(table,code,default)
        return dic

if __name__ == "__main__":
    ik = ikdata()
    ik.run()

    
    

    
    