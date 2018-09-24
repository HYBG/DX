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
import web
import json
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

class ikhq:
    def __init__(self,code,open,high,low,close,lastclose,volwy,volh,date,time):
        self.code = code
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volwy = volwy
        self.lastclose = lastclose
        self.volh = volh
        self.date = date
        self.time = time

    def zdf(self):
        return round(100*((self.close-self.lastclose)/self.lastclose),2)

class ikfund:
    def __init__(self,home='/var/data/iknow'):
        self._logger = logging.getLogger('ikfund')
        self._loglevel = logging.INFO
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logd = os.path.join(home,'log')
        logfile = os.path.join(logd,'ikfund.log')
        rh = RotatingFileHandler(logfile, maxBytes=50*1024*1024,backupCount=10)
        rh.setLevel(self._loglevel)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(self._loglevel)
        self._connection = None
        self._cursor = None
        self._conn('fund')

    def __del__(self):
        if not self._cursor:
            self._cursor.close()
        if not self._connection:
            self._connection.close()

    def _conn(self,dbname):
        try:
            self._connection = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self._logger.info('iknow connect db[%s] error[%s]'%(dbname,e))
        return False

    def _reconn(self,dbname):
        try:
            self._cursor.close()
            self._connection.close()
            self._connection = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self._logger.info('iknow reconnect db[%s] error[%s]'%(dbname,e))
        return False

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
        ret = ()
        if n>0:
            ret = self._cursor.fetchall()
        return ret
        
    def _task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    self._logger.info('iknow execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                self._logger.error('iknow execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._connection.rollback()
                return False
        self._connection.commit()
        return True

    def _query(self,userid):
        pass

    def _checkparas(self,paras,paraslist):
        for para in paraslist:
            if not paras.has_key(para):
                return False
        return True

    def put(self,paras):
        if self._checkparas(paras,['userid','code','amount','price','bors']):
            need = int(paras['amount'])*float(paras['price'])*1.01
            have = self._query(paras['userid'])
            if have>=need:
                pass
            return json.dumps({'retcode':'1011'})
        return json.dumps({'retcode':'1010'})

    def cancel(self,paras):
        if self._checkparas(paras,['orderid']):
            return json.dumps({'retcode':'1011'})
        return json.dumps({'retcode':'1010'})

    def GET(self):
        if len(web.ctx.query)==0:
            return defaultoutput({})
        paras = self._parse(web.ctx.query)
        fun = getattr(self,paras['name'],self.defaultoutput)
        return fun(paras)
        
    def POST(self):
        pass
        
if __name__ == "__main__":
    urls = (
        '/iknow', 'iknow'
    )
    app = web.application(urls, globals())
    app.run()
        
        
        