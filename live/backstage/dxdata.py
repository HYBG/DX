import os
import sys
import logging
import string
import re
import datetime
import time
import commands
import random
import urllib2
from datetime import timedelta
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
import web
import json
sys.path.append(os.path.join(g_home,'lib'))
from dxdb import dxdblib

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('dx')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'dx.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class dxresponse:
    def __init__(self):
        self._whitelist = []
        self._db = dxdblib('localhost','root','123456','dx','utf8')

    def __del__(self):
        pass
        
    def _parse(self):
        try:
            full = web.ctx.fullpath
            pair = full.split('?')
            oper = pair[0][1:]
            paras = pair[1].split('&')
            param = {}
            for ps in paras:
                kvs = ps.split('=')
                param[kvs[0]] = kvs[1]
            return (oper,param)
        except Exception,e:
            return None
            
    def _rtprice(self,code):
        

    def _create(self,param):
        uid = param['uid']
        ext = self._db.exesqlone('select count(*) from dx_user where userid=%s',(uid,))
        if ext[0] > 0:
            return {'retcode':'10010','retmessage':'user has been exist'}
        else:
            if self._db.task([('insert into dx_user(userid) values(%s)',(uid,))]):
                return {'retcode':'10000','retmessage':'successfully'}
            else:
                return {'retcode':'10001','retmessage':'system error'}

    def _deposit(self,param):
        uid = param['uid']
        money = param['money']
        if self._db.task([('update dx_user set cash = cash+%s where userid=%s',(money,uid))]):
            return {'retcode':'10000','retmessage':'successfully'}
        else:
            return {'retcode':'10001','retmessage':'system error'}

    def _open(self,param):
        uid = param['uid']
        ot = param['otype']
        code = param['code']
        amount = param['amount']
        hq = self._rtprice(code)
        if ot == '1':
            
        sqls = []
        sqls.append(('insert into dx_order_open(orderid,userid,code,amount,openprice) values(%s,%s,%s,%s,%s)',))
        if self._db.task([('update dx_user set cash = cash+%s where userid=%s',(money,uid))]):
            return {'retcode':'10000','retmessage':'successfully'}
        else:
            return {'retcode':'10001','retmessage':'system error'}
    
    def _close(self,param):
    
    def _put(self,param):
    
    def _cancel(self,param):
        
    def _set(self,param):
    
    def _query(self,param):
        
    def GET(self):
        try:
            fromip = self._db.exesqlone('select count(*) from dx_global where name=%s and value=%s',(web.ctx.ip,'1'))
            if fromip[0]==0:
                return json.dumps({'retcode':'10003','retmessage':'ip reject'})
            oper,param = self._parse()
            func = getattr(self,'_%s'%oper)
            return json.dumps(func(param))
        except Exception,e:
            g_logger.warning('system exception[%s]'%e)
            return json.dumps({'retcode':'10002','retmessage':'system exception'})

    def POST(self):
        return 'POST response'

if __name__ == "__main__":
    urls = (
    '/[create,deposit,open,put,cancel,close,set]?.*', 'dxresponse')

    app = web.application(urls, globals())
    app.run()


