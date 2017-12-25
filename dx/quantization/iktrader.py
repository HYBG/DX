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

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('iktrade')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'iktrade.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class iktrade:
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

    def _rtprice(self,code):
        market = None
        market = 'sz'
        if code[:2]=='60' or code[0]=='5':
            market = 'sh'
        url = 'http://hq.sinajs.cn/list=%s%s'%(market,code)
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            v = None
            now = datetime.datetime.now()
            if int(info[8])>0 and info[30]=='%04d-%02d-%02d'%(now.year,now.month,now.day):
                v = info
            return v
        except Exception, e:
            g_logger.warning('get current price code[%s] exception[%s]'%(code,e))
            return None

    '''
    market status 1:noon opening,2:afternoon opening,3:noon rest,4:check accounts,5:idle
    '''
    def _setmarket(self,status):
        st = self._exesqlone("select value from trader_global where name=%s",('market',))
        if int(st[0])!=status:
            self._task([('update trader_global set value=%s where name=%s',(status,'market'))])
            g_logger.info('iktrade set market[%d]'%status)

    def _opencodes(self):
        all = self._exesqlone('select code from trader_code where ststus=0',None)
        sqls = []
        for row in all:
            code = row[0]
            if self._rtprice(code):
                sqls.append(('update trader_code set status=1 where code=%s',(code,)))
            else:
                sqls.append(('update trader_code set status=2 where code=%s',(code,)))
        if len(sqls)>0:
            self._task(sqls)
        all = self._exesqlone('select code from trader_code where ststus=2',None)
        sqls = []
        for row in all:
            code = row[0]
            if self._rtprice(code):
                sqls.append(('update trader_code set status=1 where code=%s',(code,)))
        if len(sqls)>0:
            self._task(sqls)

    def _closecodes(self):
        left = self._exesqlone('select count(*) from trader_code where status!=0 and status!=3',None)
        if (left[0]!=0):
            self._task([('update trader_code set status=0',None)])

    def _dealorders(self):
        puts = self._exesqlbatch('select orderid,userid,putdate,puttime,code,amount,putprice,freeze from trader_order_put',None)
        sqls = []
        for order in puts:
            now = datetime.datetime.now()
            sqls.append(('insert into trader_order_cancel(orderid,userid,putdate,puttime,canceldate,canceltime,tag,code,amount,putprice) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(order[0],order[1],order[2],order[3],'%04d-%02d-%02d'%(now.year,now.month,now.day),'%02d:%02d:%02d'%(now.hour,now.minute,now.second),1,order[4],order[5],order[6],order[7])))
            sqls.append(('delete from trader_order_put where orderid=%s',(order[0],)))
            sqls.append(('update trader_user set cash=cash+%s where orderid=%s',(order[8],order[0])))
        sqls.append(('update trader_order_open set tag=1,surviving=surviving+1',None))
        users = self._exesqlbatch('select userid from trader_user',None)
        for us in users:
            holds = self._exesqlbatch('select code,amount from trader_order_open where userid=%s',(us[0],))
            vals = 0
            for h in holds:
                code = h[0]
                amount = h[1]
                ps = self._rtprice(code)
                vals = vals + float(ps[3])*amount
            sqls.append(('update trader_user set value=%s where userid=%s',(vals,us[0])))
        self._task(sqls)

    def _supermarket(self):
        g_logger.info('iktrade _supermarket start....')
        self._reconn()
        while 1:
            now = datetime.datetime.now()
            wd = now.isoweekday()
            restd = self._exesqlone("select count(*) from trader_global where name=%s",('%04d-%02d-%02d'%(now.year,now.month,now.day),))
            o1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=9,minute=30,second=0)
            c1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=11,minute=30,second=0)
            o2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=13,minute=0,second=0)
            c2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=0,second=0)
            che = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=17,minute=0,second=0)
            if wd!=6 and wd!=7 and restd[0]==0: #opening day
                if now>o1 and now<c1:
                    self._setmarket(1)
                    self._opencodes()
                elif now>o2 and now<c2:
                    self._setmarket(2)
                elif now>=c1 and now<=o2:
                    self._setmarket(3)
                elif now>c2 and now<che:
                    self._setmarket(4)
                    self._closecodes()
                    self._dealorders()
                #else:
                #    self._setmarket(5)
            #else: #rest
                #self._setmarket(5)
            time.sleep(2)
        g_logger.info('iktrade _supermarket end....')

    def _dealtrade(self):
        g_logger.info('iktrade _dealtrade start....')
        self._reconn()
        while 1:
            st = self._exesqlone("select value from trader_global where name=%s",('market',))
            if (int(st[0])==1 or int(st[0])==2):
                puts = self._exesqlbatch('select orderid,userid,putdate,puttime,win,lose,code,amount,putprice,freeze from trader_order_put',None)
                sqls = []
                for order in puts:
                    now = datetime.datetime.now()
                    dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
                    tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
                    ps = self._rtprice(order[6])
                    if order[8]>=float(ps[7]):
                        sqls.append(('insert into trader_order_open(orderid,userid,putdate,puttime,opendate,opentime,win,lose,code,amount,openprice) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(order[0],order[1],order[2],order[3],'%04d-%02d-%02d'%(now.year,now.month,now.day),'%02d:%02d:%02d'%(now.hour,now.minute,now.second),order[5],order[6],order[7],order[8],ps[7])))
                        if (order[8]>float(ps[7])):
                            sid = self._buildid('S')
                            left = '%.2f'%(order[8]-float(ps[7]))
                            sqls.append(('insert into trader_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,order[0],dt,tm,left)))
                            sqls.append(('update trader_user set cash=cash+%s',(left,)))
                        sqls.append(('delete from trader_order_put where orderid=%s',(order[0],)))
                        self._task(sqls)
                opens = self._exesqlbatch('select orderid,userid,opendate,opentime,win,lose,code,amount,openprice from trader_order_open where tag=1',None)
                sqls = []
                for order in opens:
                    now = datetime.datetime.now()
                    dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
                    tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
                    ps = self._rtprice(order[6])
                    if (len(str(order[4]))>0 and order[4]<=float(ps[6])) or (len(str(order[5]))>0 and order[5]>=float(ps[6])):
                        close = float(ps[6])
                        left = close*order[7]
                        comms = left*0.0015
                        earn = (close-order[8])*order[7]-comms
                        sqls.append(('insert into trader_order_close(orderid,userid,opendate,opentime,closedate,closetime,code,amount,openprice,closeprice,commission,earn) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(order[0],order[1],order[2],order[3],'%04d-%02d-%02d'%(now.year,now.month,now.day),'%02d:%02d:%02d'%(now.hour,now.minute,now.second),order[7],order[8],order[9],close,'%0.3f'%comms,'%0.3f'%earn)))
                        sqls.append(('update trader_user set cash=cash+%s',('%0.2f'%left,)))
                        sid = self._buildid('S')
                        sqls.append(('insert into trader_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,order[0],dt,tm,'%0.2f'%left)))
                        sqls.append(('delete from trader_order_open where orderid=%s',(order[0],)))
                        self._task(sqls)
            time.sleep(1)
        g_logger.info('iktrade _dealtrade end....')
    
    def run(self):
        g_logger.info('iktrade start....')
        pid = os.fork()
        if pid==0:
            try:
                self._supermarket()
            except Exception,e:
                g_logger.error('child process exception[%s]...'%e)
        else:
            try:
                self._dealtrade()
            except Exception,e:
                g_logger.error('father process exception[%s]...'%e)
        g_logger.info('iktrade exit....')

if __name__ == "__main__":
    iktrade().run()


