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
#import MySQLdb
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')

sys.path.append(os.path.join(g_home,'lib'))
from iktraderlib import iktrader
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('iksnow1')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'iksnow1.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class iksnow1:
    def __init__(self):
        self._trader = iktrader()
        self._uid = 'snow-1'
        self._last = None
    
    def __del__(self):
        pass

    def plan(self):
        next = self._trader.next()
        if self._last == next:
            return
        now = datetime.datetime.now()
        td = '%04d-%02d-%02d'%(now.year,now.month,now.day)
        buys = self._trader.exesqlbatch('select code,score,ranking,volyy from ikbill_after where date=%s and code in (select code from ikbill_ops where date=%s and ops=1) order by ranking',(td,td))
        sells = self._trader.exesqlbatch('select code,score,ranking,volyy from ikbill_after where date=%s and code in (select code from ikbill_ops where date=%s and ops=2) order by ranking',(td,td))
        accs = self._trader.query(self._uid)
        cash = accs[0][0]
        value = accs[0][1]
        holds = accs[1]
        for h in holds:
            orderid = h[0]
            code = h[1]
            amount = h[2]
            bprice = h[3]
            sur = h[4]
            tinf = self._trader.exesqlone('select close,zdf,zf,hs,high,low from ikbill_data where code=%s and date=%s',(code,td))
            close = tinf[0]
            rng = self._trader.exesqlone('select crn,hrn,lrn from ikbill_ops where code=%s and date=%s',(code,td))
            ps = self._trader.exesqlone('select c1_ev,c1_std,h1_ev,h1_std,l1_ev,l1_std from ikbill_tell where code=%s and date=%s',(code,td))
            lose = close*(1+(float(ps[4])-float(ps[5]))/100)
            settag = False
            for sl in sells:
                if code == sl[0]:
                    if len(sells)>400:
                        win = rng[0]
                        if win<close:
                            win = close
                        self._trader.set(orderid,win,lose)
                    else:
                        self._trader.set(orderid,rng[1],lose)
                    settag = True
                    break
            if sur>=5:
                self._trader.set(orderid,close,lose)
            elif not setag:
                wwin = close*(1+(float(ps[2])+2*float(ps[3]))/100)
                self._trader.set(orderid,wwin,lose)
        if len(buys)>450:
            all = cash+value
            while cash > all*0.2:
                use = all*0.2
                item = buys.pop()
                code = item[0]
                #ps = self._trader.exesqlone('select c1_ev,c1_std,h1_ev,h1_std,l1_ev,l1_std from ikbill_tell where code=%s and date=%s',(code,td))
                close = self._trader.exesqlone('select close from ikbill_data where code=%s and date=%s',(code,td))
                close = close[0]
                amount = int((use/close)/100)*100
                self._trader.put(self._uid,code,amount,close)
                cash = cash-close*amount
            if cash > all*0.1:
                item = buys.pop()
                code = item[0]
                close = self._trader.exesqlone('select close from ikbill_data where code=%s and date=%s',(code,td))
                close = close[0]
                amount = int((use/close)/100)*100
                self._trader.put(self._uid,code,amount,close)
        self._last = next
        g_logger.info('plan for next day[%s] is done....'%(self._last))

    def run(self):
        g_logger.info('iksnow1 start....')
        ext = self._trader.exesqlone('select count(*) from trader_user where userid=%s',(self._uid,))
        if ext[0]==0:
            self._trader.create(self._uid)
            self._trader.deposit(self._uid,1000000)
        while 1:
            st = self._trader.market()
            if st == 5:
                self.plan()
            time.sleep(2)
        g_logger.info('iksnow1 exit....')

if __name__ == "__main__":
    iksnow1().run()


