#!/usr/bin/python

import os
import sys
import urllib2
import logging
import string
import re
import datetime
import time
import random
import socket
import commands
import MySQLdb
import hashlib
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
import smtplib  
from email.mime.text import MIMEText

HY_TRADER_ORDER_PUT = 1000
HY_TRADER_ORDER_OPEN = 1001
HY_TRADER_ORDER_CANCEL = 1002
HY_TRADER_ORDER_CLOSE = 1003
HY_TRADER_ORDER_WAITING_PUT = 1100
HY_TRADER_ORDER_OPEN_WITH_RT = 1101
HY_TRADER_ORDER_OPEN = 1004
HY_TRADER_ORDER_ACTION_BUY = 0
HY_TRADER_ORDER_ACTION_SELL = 1
HY_TRADER_RETCODE_SUCCESS = 0
HY_TRADER_RETCODE_ORDER_STATUS_ERROR = 1
HY_TRADER_RETCODE_DB_OPERATION_ERROR = 2
HY_TRADER_RETCODE_USER_NOT_EXIST = 3
HY_TRADER_RETCODE_CASH_NOT_ENOUGH = 4
HY_TRADER_RETCODE_TRADE_FAILURE = 5
HY_TRADER_RETCODE_ORDER_NOT_EXIST = 6

class hyrt(object):
    def __init__(self,code,date,time,open,high,low,close,buy,sell,vol,volh,lastclose):
        self.code = code
        self.date = date
        self.time = time
        self.open = open
        self.high = high
        self.low  = low
        self.close = close
        self.buy = buy
        self.sell = sell
        self.vol = vol
        self.volh = volh
        self.lastclose = lastclose
        
class hyorder(object):
    def __init__(self,oid,uid,action,win,lose,code,amount,holddays):
        self.orderid = oid
        self.userid = uid
        self.action = action
        self.win = win
        self.lose = lose
        self.code = code
        self.amount = amount
        self.holddays = holddays
        self.putprice = None
        self.openprice = None
        self.closeprice = None
        self.puttime = None
        self.opentime = None
        self.closetime = None
        self.commission = None
        self.earn = None
        self.rate = None
        self.status = None

class hytraderlib(object):
    def __init__(self):
        self._conn = None
        self._cursor = None
        self._logger = logging.getLogger('hytraderlib')
        self._loglevel = logging.INFO
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logfile = os.path.join('/var/log','hytraderlib.log')
        rh = RotatingFileHandler(logfile, maxBytes=50*1024*1024,backupCount=10)
        rh.setLevel(self._loglevel)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(self._loglevel)

    def __del__(self):
        if not self._cursor:
            self._cursor.close()
        if not self._conn:
            self._conn.close()
            
    def _createorderid(self):
        now = datetime.datetime.now()
        return "%04d%02d%02d%02d%02d%02d%06d%04d"%(now.year,now.month,now.day,now.hour,now.minute,now.second,now.microsecond,random.randint(1000,9999))

    def _loadopen(self,orderid):
        data = self.exesqlone('select orderid,userid,puttime,opentime,action,win,lose,code,amount,openprice,commission,surviving,holddays from trader.trader_order_open where orderid=%s',(orderid,))
        if len(data)==0:
            return HY_TRADER_RETCODE_ORDER_NOT_EXIST
        ho = hyorder(data[0],data[1],data[4],data[5],data[6],data[7],data[8],data[12])
        ho.puttime = data[2]
        ho.opentime = data[3]
        ho.openprice = data[9]
        ho.surviving = data[11]
        ho.status = HY_TRADER_ORDER_OPEN
        return ho
        
    def _loadput(self,orderid):
        data = self.exesqlone('select orderid,userid,puttime,action,win,lose,code,amount,putprice,freeze,holddays from trader.trader_order_put where orderid=%s',(orderid,))
        if len(data)==0:
            return HY_TRADER_RETCODE_ORDER_NOT_EXIST
        hp = hyorder(data[0],data[1],data[3],data[4],data[5],data[6],data[7],data[10])
        hp.puttime = data[2]
        hp.putprice = data[8]
        hp.freeze = data[9]
        hp.status = HY_TRADER_ORDER_PUT
        return hp

    def conn(self):
        try:
            self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='trader',charset='utf8') 
            self._cursor = self._conn.cursor()
            return True
        except Exception,e:
            self._logger.error('hytraderlib connect db[%s] error[%s]'%(dbname,e))
        return False
        
    def reconn(self):
        try:
            self._cursor.close()
            self._conn.close()
            self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='trader',charset='utf8') 
            self._cursor = self._conn.cursor()
            return True
        except Exception,e:
            self._logger.error('hytraderlib reconnect db[%s] error[%s]'%(dbname,e))
        return False

    def createlogger(self,logname,filename,level):
        logger = logging.getLogger(logname)
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        rh = RotatingFileHandler(filename, maxBytes=100*1024*1024,backupCount=50)
        rh.setLevel(level)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        logger.addHandler(rh)
        logger.setLevel(level)
        return logger
        
    def openaccount(self,deposit):
        hl = hashlib.md5()
        userid = self._createorderid()
        hl.update(userid.encode(encoding='utf-8'))
        userid = hl.hexdigest()
        sqls = []
        sql.append(('insert into tarder.trader_user(userid,cash) values(%s,%s)',(userid,deposit)))
        return self.task(sqls)

    def createorder(self,userid,action,win,lose,code,amount,holddays,price):
        orderid = self._createorderid()
        ho = hyorder(orderid,userid,action,win,lose,code,amount,holddays)
        if price:
            ho.putprice = price
            ho.status = HY_TRADER_ORDER_WAITING_PUT
        else:
            ho.status = HY_TRADER_ORDER_OPEN_WITH_RT
        return ho

    def put(self,order):
        if order.status == HY_TRADER_ORDER_WAITING_PUT:
            left = self.exesqlone('select cash from trader.trader_user where userid=%s',(order.userid,))
            freeze = order.putprice*order.amount*100+order.commission
            if len(left)==0:
                return HY_TRADER_RETCODE_USER_NOT_EXIST
            if left[0]<freeze:
                return HY_TRADER_RETCODE_CASH_NOT_ENOUGH
            sqls = []
            sqls.append(('insert into trader.trader_order_put(orderid,userid,win,lose,action,code,amount,putprice,freeze,holddays) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(order.orderid,order.userid,order.win,order.lose,order.action,order.code,order.amount,order.putprice,freeze,order.holddays)))
            sqls.append(('update trader.trader_user set cash=%s where userid=%s',(left[0]-freeze,order.userid)))
            if self.task(sqls):
                return HY_TRADER_RETCODE_SUCCESS
            else:
                return HY_TRADER_RETCODE_DB_OPERATION_ERROR
        else:
            return HY_TRADER_RETCODE_ORDER_STATUS_ERROR

    def open(self,order):
        if order.status == HY_TRADER_ORDER_OPEN_WITH_RT:
            rt = self.rtprice(order.code)
            if not rt:
                return HY_TRADER_RETCODE_TRADE_FAILURE
            openprice = rt.buy
            if order.action == HY_TRADER_ORDER_ACTION_BUY:
                openprice = rt.sell
            left = self.exesqlone('select cash from trader.trader_user where userid=%s',(order.userid,))
            value = 100*order.amount*openprice
            commission = 0.003*value
            if len(left)==0:
                return HY_TRADER_RETCODE_USER_NOT_EXIST
            if left[0]<value+commission:
                return HY_TRADER_RETCODE_CASH_NOT_ENOUGH
            sqls = []
            sqls.append(('insert into trader.trader_order_open(orderid,userid,win,lose,action,code,amount,openprice,commission,holddays) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(order.orderid,order.userid,order.win,order.lose,order.action,order.code,order.amount,order.openprice,commission,order.holddays)))
            sqls.append(('update trader.trader_user set cash=%s where userid=%s'),(left[0]-value-commission,order.userid))
            if self.task(sqls):
                return HY_TRADER_RETCODE_SUCCESS
            else:
                return HY_TRADER_RETCODE_DB_OPERATION_ERROR
        else:
            return HY_TRADER_RETCODE_ORDER_STATUS_ERROR

    def close(self,orderid):
        ho = self._loadopen(orderid)
        sqls = []
        rt = self.rtprice(order.code)
        if not rt:
            return HY_TRADER_RETCODE_TRADE_FAILURE
        closeprice = rt.sell
        earn = (ho.openprice-closeprice)*ho.amount*100-ho.commission
        if order.action == HY_TRADER_ORDER_ACTION_BUY:
            closeprice = rt.buy
            earn = (closeprice-ho.openprice)*ho.amount*100-ho.commission
        rate = float('%0.2f'%(100*(earn/(ho.openprice*ho.amount*100-ho.commission))))
        if ho.puttime:
            sqls.append(('insert into trader.trader_order_close(orderid,userid,puttime,opentime,action,win,lose,code,amount,openprice,closeprice,commission,earn,rate,surviving,holddays) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',()))
        else:
            sqls.append(('insert into trader.trader_order_close(orderid,userid,opentime,action,win,lose,code,amount,openprice,closeprice,commission,earn,rate,surviving,holddays) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',()))
        sqls.append(('update trader.trader_user set cash=cash+%s where userid=%s',()))
        sqls.append(('delete from trader.trader_order_open where orderid=%s',(orderid,)))
        if self.task(sqls):
            return HY_TRADER_RETCODE_SUCCESS
        else:
            return HY_TRADER_RETCODE_DB_OPERATION_ERROR

    def cancel(self,orderid):
        hp = self._loadput(orderid)
        sqls = []
        sqls.append(('insert into trader.trader_order_cancel(orderid,userid,puttime,win,lose,action,code,amount,putprice,holddays) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',()))
        sqls.append(('update trader.trader_user set cash=cash+%s where userid=%s'),())
        sqls.append(('delete from trader.trader_order_put where orderid=%s',(orderid,)))
        if self.task(sqls):
            return HY_TRADER_RETCODE_SUCCESS
        else:
            return HY_TRADER_RETCODE_DB_OPERATION_ERROR

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
        ret = ()
        if n>0:
            ret = self._cursor.fetchall()
        return ret
        
    def task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    g_logger.info('hytraderlib execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                g_logger.error('hytraderlib execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._conn.rollback()
                return False
        self._conn.commit()
        return True

    def isopenday(self):
        now = datetime.datetime.now()
        wd = now.isoweekday()
        o1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=9,minute=30,second=0)
        c2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=0,second=0)
        if wd == 6 or wd == 7:
            return False
        if now < o1 or now > c2:
            return False
        url = 'http://hq.sinajs.cn/list=sz399001'
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            if info[30] == '%04d-%02d-%02d'%(now.year,now.month,now.day):
                return True
        except Exception, e:
            self.log(logging.WARNING,'get current url[%s] exception[%s]'%(url,e))
            return None

    def rtprice(self,code):
        market = None
        if code[:2]=='60' or code[0]=='5':
            market = 'sh'
        else:
            market = 'sz'
        url = 'http://hq.sinajs.cn/list=%s%s'%(market,code)
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            return hyrt(code,info[30],info[31],float(info[1]),float(info[4]),float(info[5]),float(info[3]),float(info[7]),float(info[6]),float(info[9]),float(info[8]),float(info[2]))
        except Exception, e:
            self.log(logging.WARNING,'get current price code[%s] exception[%s]'%(code,e))
            return None
            
    def _rtprice(self,codes):
        codeliststr = ''
        for code in codes:
            market = None
            if code[:2]=='60' or code[0]=='5':
                market = 'sh'
            else:
                market = 'sz'
            codeliststr = codeliststr + '%s%s,'%(market,code)
        url = 'http://hq.sinajs.cn/list=%s'%(codeliststr[:-1])
        self.log(logging.INFO,'_rtprice url[%s]'%(url))
        data = urllib2.urlopen(url).readlines()
        i = 0
        lis = []
        for line in data:
            info = line.split('"')[1].split(',')
            now = datetime.datetime.now()
            if int(info[8])>0 and info[30]=='%04d-%02d-%02d'%(now.year,now.month,now.day):
                code = codes[i]
                yc = float(info[2])
                open = float(info[1])
                high = float(info[4])
                low = float(info[5])
                close = float(info[3])
                volh = float(info[8])
                volwy = float(info[9])
                v = (code,'%s %s'%(info[30],info[31]),code,open,high,low,close,volh,volwy,yc)
                lis.append(v)
            i = i+1
        return lis
            
    def rtpricebatch(self,codes):
        try:
            thv = 800
            n = (len(codes)/thv)+1
            lis = []
            for i in range(n):
                start = i*thv
                cs = codes[start:start+thv]
                l = self._rtprice(cs)
                lis = lis+l
            return lis
        except Exception, e:
            self.log(logging.WARNING,'get current price codes exception[%s]'%(e))
            return None

if __name__ == "__main__":
    tl = iktool()
    tl.conn('dx')
    code='600111'
    begin = '2018-01-01'
    need = tl.exesqlbatch('select date from dx.iknow_data where code=%s and date>%s',(code,begin))
    have = tl.exesqlbatch('select date from dx.iknow_attr where code=%s',(code))
    list(set(need).difference(set(have)))





        