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
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('ikmom')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'ikmom.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class ikmomplan:
    def __init__(self,pid,dy,buylis,selllis):
        self.day = dy
        self.pid = pid
        self.buylis = buylis
        self.selllis = selllis

class ikmomutil:
    def __init__(self):
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()

    def _reconn(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()

    def log(self,level,str):
        g_logger.log(level,str)

    def link(self,dir,link,target):
        cwd = os.getcwd()
        os.chdir(dir)
        cmd = 'ln -snf %s %s'%(target,link)
        status,output = commands.getstatusoutput(cmd)
        g_logger.info('execute cmd[%s] status[%d] output[%s]'%(cmd,status,output))
        os.chdir(cwd)

    def mkdir(self,dir):
        if not os.path.isdir(dir):
            os.makedirs(dir)

    def execmd(self,cmd):
        status,output = commands.getstatusoutput(cmd)
        g_logger.info('execute command[%s],status[%d],output[%s]'%(cmd,status,output.strip()))
        return status
        
    def _exesqlone(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchone()
        
    def _exesqlbatch(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchall()
        
    def nextday(self):
        now = datetime.datetime.now()
        rests = self._exesqlbatch('select date from ikmom_rest where date>=%s',('%04d-%02d-%02d'%(now.year,now.month,now.day),))
        rs = []
        for r in rests:
            rs.append(r[0])
        next = now
        timespan = datetime.timedelta(days=1)
        if now.hour >= 9:
            next = now+timespan
        str = '%04d-%02d-%02d'%(next.year,next.month,next.day)
        wd = next.isoweekday()
        while wd==6 or wd==7 or (str in rs):
            next = next+timespan
            wd = next.isoweekday()
            str = '%04d-%02d-%02d'%(next.year,next.month,next.day)
        return str
        
    def isduring(self,dy):
        ymd = dy.split('-')
        o1 = datetime.datetime(year=int(ymd[0]),month=int(ymd[1]),day=int(ymd[2]),hour=9,minute=30,second=0)
        c1 = datetime.datetime(year=int(ymd[0]),month=int(ymd[1]),day=int(ymd[2]),hour=11,minute=30,second=0)
        o2 = datetime.datetime(year=int(ymd[0]),month=int(ymd[1]),day=int(ymd[2]),hour=13,minute=0,second=0)
        c2 = datetime.datetime(year=int(ymd[0]),month=int(ymd[1]),day=int(ymd[2]),hour=15,minute=0,second=0)
        now = datetime.datetime.now()
        if now < o1:
            return 0 #0:before open,1:rest of noon.2:opening,3:close
        elif now > c2:
            return 3
        elif now > c1 and now < o2:
            return 1
        else:
            return 2

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
            v = (info[-3],float(info[1]),float(info[4]),float(info[5]),float(info[3]),int(info[8]),float(info[2]))
            return v
        except Exception, e:
            g_logger.warning('get current price code[%s] exception[%s]'%(code,e))
            return None
            
    def _buy(self,code,amount,price):
        pass

    def _sell(self,code,amount,price):
        pass
        
    def _money(self,pid):
        pass

    def exeplan(self,plan):
        sl = []
        for sp in plan.selllis:
            code = sp[0]
            amount = sp[1]
            price = sp[2]
            lose = sp[3]
            prc = self.rtprice(code)
            cp = prc[4]
            if cp>price:
                self._sell(code,amount,cp)
            elif cp<=lose:
                self._sell(code,amount,cp)
            else:
                sl.append(sp)
        plan.selllis = sl
        money = self._money(plan.pid)
        bl = []
        for bp in plan.buylis:
            code = bp[0]
            amount = bp[1]
            price = bp[2]
            prc = self.rtprice(code)
            cp = prc[4]
            if cp<=price:
                need = cp*amount*1.0003
                if money>=need:
                    self._buy(code,amount,cp)
                    money = money-need
                elif money<cp*100*1.0003:
                    bl.append(bp)
                else:
                    amount = 100*((int(money/(1.0003*cp)))/100)
                    used = cp*amount*1.0003
                    self._buy(code,amount,cp)
                    money = money-used
            else:
                bl.append(bp)
        plan.buylis = bl
            
    def buildplan(self,pid,dy):
        if pid == 'P2017110815544010199':
            pass


            

